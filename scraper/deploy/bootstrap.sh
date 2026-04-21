#!/usr/bin/env bash
# Buyr scraper bootstrap script — Oracle Cloud Ubuntu ARM
# Installs Docker (if missing), iptables rules, Caddy; builds & runs the scraper;
# configures HTTPS via Caddy for scraper.buyrs.app.
#
# Usage:
#   SUPABASE_URL=... SUPABASE_SERVICE_KEY=... GOOGLE_MAPS_API_KEY=... \
#     bash bootstrap.sh
#
# Optional:
#   SCRAPER_API_SECRET=...    # auto-generated if unset
#   REPO_URL=https://github.com/nealcaffery2/buyr.git
#   BRANCH=claude/setup-cloudflare-vercel-domain-DGulX
#   SCRAPER_DOMAIN=scraper.buyrs.app

set -euo pipefail

: "${REPO_URL:=https://github.com/nealcaffery2/buyr.git}"
: "${BRANCH:=claude/setup-cloudflare-vercel-domain-DGulX}"
: "${SCRAPER_DOMAIN:=scraper.buyrs.app}"
: "${REPO_DIR:=$HOME/buyr}"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# ---- Sanity checks ----------------------------------------------------------
[[ -n "${SUPABASE_URL:-}" ]] || die "SUPABASE_URL is required"
[[ -n "${SUPABASE_SERVICE_KEY:-}" ]] || die "SUPABASE_SERVICE_KEY is required"
[[ -n "${GOOGLE_MAPS_API_KEY:-}" ]] || die "GOOGLE_MAPS_API_KEY is required"
[[ -n "${BATCH_DATA_API_KEY:-}" ]] || die "BATCH_DATA_API_KEY is required"

if [[ -z "${SCRAPER_API_SECRET:-}" ]]; then
  SCRAPER_API_SECRET="$(openssl rand -hex 32)"
  log "Generated SCRAPER_API_SECRET (save this for Vercel):"
  echo "    $SCRAPER_API_SECRET"
fi

# ---- iptables: open 80/443 above Oracle's default REJECT rule --------------
log "Configuring iptables for ports 80/443"
if ! sudo iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null; then
  sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT
fi
if ! sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null; then
  sudo iptables -I INPUT 5 -p tcp --dport 443 -j ACCEPT
fi
# Persist across reboots
if ! dpkg -s iptables-persistent >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
fi
sudo netfilter-persistent save

# ---- Docker -----------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker"
  sudo apt-get update
  sudo apt-get install -y docker.io
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$USER"
  log "Added $USER to docker group — you may need to log out/in for non-sudo docker"
fi

# ---- Repo -------------------------------------------------------------------
if [[ ! -d "$REPO_DIR/.git" ]]; then
  log "Cloning $REPO_URL (branch $BRANCH)"
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
else
  log "Repo exists, pulling latest on $BRANCH"
  git -C "$REPO_DIR" fetch origin "$BRANCH"
  git -C "$REPO_DIR" checkout "$BRANCH"
  git -C "$REPO_DIR" pull --ff-only origin "$BRANCH"
fi

# ---- .env -------------------------------------------------------------------
log "Writing $REPO_DIR/scraper/.env"
cat > "$REPO_DIR/scraper/.env" <<EOF
SUPABASE_URL=$SUPABASE_URL
SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY
API_SECRET=$SCRAPER_API_SECRET
GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY
BATCH_DATA_API_KEY=$BATCH_DATA_API_KEY
EOF
chmod 600 "$REPO_DIR/scraper/.env"

# ---- Build & run container --------------------------------------------------
log "Building Docker image (this takes ~5-10 min on ARM)"
sudo docker build -t buyr-scraper "$REPO_DIR/scraper"

log "Stopping any previous scraper container"
sudo docker rm -f scraper 2>/dev/null || true

log "Starting scraper container on 127.0.0.1:8000"
sudo docker run -d \
  --name scraper \
  --restart unless-stopped \
  --env-file "$REPO_DIR/scraper/.env" \
  -p 127.0.0.1:8000:8000 \
  buyr-scraper

sleep 3
log "Local health check"
curl -sf http://127.0.0.1:8000/health || die "Scraper did not return 200 on /health — check: sudo docker logs scraper"

# ---- Caddy (HTTPS reverse proxy) -------------------------------------------
if ! command -v caddy >/dev/null 2>&1; then
  log "Installing Caddy"
  sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl gnupg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y caddy
fi

log "Writing /etc/caddy/Caddyfile for $SCRAPER_DOMAIN"
sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
$SCRAPER_DOMAIN {
    reverse_proxy 127.0.0.1:8000
    encode zstd gzip
}
EOF

sudo systemctl restart caddy
sleep 2
sudo systemctl is-active --quiet caddy && log "Caddy is running" || die "Caddy failed to start — check: sudo journalctl -u caddy -n 50"

# ---- Done -------------------------------------------------------------------
cat <<EOF

===============================================================================
BOOTSTRAP COMPLETE

Next manual steps:

1. Cloudflare DNS — add A record:
     scraper  ->  $(curl -s https://ifconfig.me)   (DNS only / grey cloud initially)
   Delete the two stray A records on buyrs.app (13.248.243.5 and 76.223.105.230).
   SSL/TLS mode: Full (strict).

2. Wait ~60 seconds, then from anywhere:
     curl -I https://$SCRAPER_DOMAIN/health
   Once that returns 200, flip the scraper record in Cloudflare to Proxied (orange).

3. Vercel env vars (Settings -> Environment Variables):
     NEXT_PUBLIC_SCRAPER_API_URL = https://$SCRAPER_DOMAIN
     SCRAPER_API_SECRET          = $SCRAPER_API_SECRET

   Redeploy the Vercel project.

===============================================================================
EOF
