"""
Skip trace orchestrator.
Priority: BatchData → PropStream → DealMachine.
Stops as soon as one provider returns results with phones.
"""
from dataclasses import asdict
from .batchdata import skip_trace_name, skip_trace_llc, SkipTraceResult
from .propstream import skip_trace_person as ps_skip
from .dealmachine import skip_trace_person as dm_skip


async def get_contacts(
    agent_name: str,
    agent_address: str,
    llc_name: str,
    state: str,
    api_keys: dict,
) -> list[dict]:
    """
    Try all skip trace providers in priority order.
    Returns list of contact dicts ready for DB insertion.
    """
    results: list[SkipTraceResult] = []

    # 1. BatchData — try person first, then LLC entity
    bd_key = api_keys.get("batchdata_api_key", "")
    if bd_key:
        if agent_name:
            results = await skip_trace_name(agent_name, agent_address, bd_key)
        if not results:
            results = await skip_trace_llc(llc_name, state, bd_key)

    # 2. PropStream — if BatchData had no phones
    if not any(r.phone for r in results):
        ps_email = api_keys.get("propstream_email", "")
        ps_pass = api_keys.get("propstream_password", "")
        if ps_email and ps_pass and agent_name:
            ps_results = await ps_skip(agent_name, agent_address, ps_email, ps_pass)
            if ps_results:
                results = [
                    SkipTraceResult(
                        name=r.name,
                        phone=r.phone,
                        email=r.email,
                        address=r.address,
                        source="propstream",
                        confidence=r.confidence,
                    )
                    for r in ps_results
                ]

    # 3. DealMachine — last resort
    if not any(r.phone for r in results):
        dm_key = api_keys.get("dealmachine_api_key", "")
        if dm_key and agent_name:
            dm_results = await dm_skip(agent_name, agent_address, dm_key)
            if dm_results:
                results = [
                    SkipTraceResult(
                        name=r.name,
                        phone=r.phone,
                        email=r.email,
                        address=r.address,
                        source="dealmachine",
                        confidence=r.confidence,
                    )
                    for r in dm_results
                ]

    return [asdict(r) for r in results]
