import "dotenv/config";
import Anthropic from "@anthropic-ai/sdk";
import { betaZodTool } from "@anthropic-ai/sdk/helpers/beta/zod";
import FirecrawlApp from "@mendable/firecrawl-js";
import { z } from "zod";

const args = Object.fromEntries(
  process.argv.slice(2).reduce<Array<[string, string]>>((acc, arg, i, arr) => {
    if (arg.startsWith("--")) acc.push([arg.slice(2), arr[i + 1]]);
    return acc;
  }, []),
);

const url = args.url;
const grantor = args.grantor;
const from = args.from;
const to = args.to;

if (!url || !grantor || !from || !to) {
  console.error(
    'Usage: npm run search -- --url "<portal URL>" --grantor "<LLC NAME>" --from MM/DD/YYYY --to MM/DD/YYYY',
  );
  process.exit(1);
}

const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });
const anthropic = new Anthropic();

const scrape = betaZodTool({
  name: "scrape",
  description:
    "Load a URL in a headless browser and return the rendered HTML (and a screenshot). Optionally run a sequence of browser actions first — click a selector, type text, press a key, wait for a selector or ms, scroll — to drive forms/pickers before extracting results. Use this to recon a search page, fill the grantor search form, submit it, and extract the results table.",
  inputSchema: z.object({
    url: z.string().url(),
    actions: z
      .array(
        z.union([
          z.object({ type: z.literal("wait"), milliseconds: z.number().optional(), selector: z.string().optional() }),
          z.object({ type: z.literal("click"), selector: z.string() }),
          z.object({ type: z.literal("write"), text: z.string(), selector: z.string().optional() }),
          z.object({ type: z.literal("press"), key: z.string() }),
          z.object({ type: z.literal("scroll"), direction: z.enum(["up", "down"]).optional() }),
          z.object({ type: z.literal("scrape") }),
          z.object({ type: z.literal("screenshot") }),
          z.object({ type: z.literal("executeJavascript"), script: z.string() }),
        ]),
      )
      .optional()
      .describe("Optional sequence of browser actions to perform before extracting the final page."),
  }),
  run: async ({ url, actions }) => {
    try {
      const res: any = await firecrawl.scrapeUrl(url, {
        formats: ["html", "markdown"],
        actions: actions as any,
        onlyMainContent: false,
        waitFor: 2000,
      });
      if (!res?.success) return `FIRECRAWL_ERROR: ${JSON.stringify(res)}`;
      const html: string = res.html ?? "";
      const md: string = res.markdown ?? "";
      const trimmed = html.length > 60_000 ? html.slice(0, 60_000) + "\n...[truncated]" : html;
      return `URL: ${url}\n--- MARKDOWN ---\n${md.slice(0, 20_000)}\n--- HTML ---\n${trimmed}`;
    } catch (e: any) {
      return `FIRECRAWL_ERROR: ${e?.message ?? String(e)}`;
    }
  },
});

const system = `You are a property-records research agent. Your job is to find every transaction where a given COMPANY is the GRANTOR (seller) on a county public-records portal between two dates, then rank the GRANTEES (buyers) by transaction count.

Use the \`scrape\` tool to drive the portal. Strategy:

1. Scrape the portal URL (no actions) to see the search form HTML. Identify the grantor input, date range fields, department/record-type selector (look for "Land Records", "Real Property", "Deeds"), and the search button.
2. If the site has autocomplete on the grantor field (common on publicsearch.us, Tyler, Landmark, Kofile), scrape again with actions: click the grantor input, write the LLC name (try ALL CAPS if no match), wait for the dropdown, click the matching suggestion, confirm the chip appears.
3. Fill the date range. Prefer typing directly; fall back to clicking the calendar icon and navigating via year/month dropdowns.
4. Ensure the department/record-type is set to land records / deeds.
5. Click the search button. Wait for results.
6. Set page size to the maximum (250 on publicsearch.us) if the control exists.
7. Extract every result row: grantee name, doc type, recorded date, doc number, address.
8. Paginate until done. On publicsearch.us you can change the URL's \`offset\` param. On others, click the next-page control.
9. Focus on DEED-type records for the ranking (DEED, WARRANTY DEED, SPECIAL WARRANTY DEED, CORRECTION DEED). Flag non-deed rows in the notes section.
10. If you hit a CAPTCHA, cookie banner blocking interaction, or a login wall — stop and report it.

Count grantees, sort descending by count, alphabetical within ties. Output this exact format:

\`\`\`
SEARCH SUMMARY
──────────────────────────────────────
Grantor Searched: <NAME>
Date Range: <START> to <END>
Portal: <URL>
Total Transactions Found: <N>
Document Types: <list>

TOP BUYERS BY TRANSACTION VOLUME
──────────────────────────────────────
Rank | Buyer Name                        | # Tx | Doc Numbers
1    | <NAME>                            | <N>  | <comma-separated>
2    | ...

SINGLE-TRANSACTION BUYERS: <count> buyers appeared once.

NOTES:
- <non-deed flags, missing grantees, data quality notes>
\`\`\`

Do NOT write code. Do NOT fabricate results. If the portal is the wrong kind of site (tax/appraisal instead of recorder/clerk — no grantor/grantee fields), say so and stop.`;

const user = `Find grantor→grantee transactions for this company.

Portal URL: ${url}
Grantor (seller): ${grantor}
Date range: ${from} to ${to}

Run the search, extract every matching record, and return the ranked buyer list.`;

console.error(`[running] ${grantor} @ ${url} (${from} → ${to})\n`);

const finalMessage = await anthropic.beta.messages.toolRunner({
  model: "claude-opus-4-7",
  max_tokens: 16000,
  thinking: { type: "adaptive" },
  system,
  tools: [scrape],
  messages: [{ role: "user", content: user }],
});

for (const block of finalMessage.content) {
  if (block.type === "text") process.stdout.write(block.text);
}
process.stdout.write("\n");
