# Cloudflare Worker - Installer Service

This Cloudflare Worker serves the installer script for advance-image-viewer, allowing users to install via:

**Linux/macOS:**

```bash
curl https://advance-image-viewer.gossorg.in | bash
```

**Windows:**

```powershell
irm https://advance-image-viewer.gossorg.in | iex
```

The worker automatically detects the platform via User-Agent and serves the appropriate installer.

## Setup

1. Install Wrangler CLI:
```bash
npm install -g wrangler
```

2. Authenticate with Cloudflare:
```bash
wrangler login
```

3. Deploy the worker:
```bash
wrangler deploy
```

## Custom Domain (Optional)

To use a custom domain like `install.advance-image-viewer.com`:

1. Add your domain in Cloudflare dashboard
2. Update `wrangler.toml` with the route:
```toml
routes = [
  { pattern = "install.advance-image-viewer.com", custom_domain = true }
]
```

3. Deploy again

## Endpoints

- `GET /` - Returns installer script (auto-detects platform via User-Agent)
- `GET /install.sh` - Returns Linux/macOS bash installer
- `GET /install` - Returns Linux/macOS bash installer
- `GET /install.ps1` - Returns Windows PowerShell installer
- `GET /install-windows.ps1` - Returns Windows PowerShell installer
- `GET /health` - Health check endpoint

### Platform Detection

The worker detects Windows via:
- User-Agent header (contains "Windows", "Win64", or "Win32")
- Explicit path requests (`/install.ps1` or `/install-windows.ps1`)

All other requests default to the Linux/macOS bash installer.

## Development

Run locally:
```bash
wrangler dev
```

Tail logs:
```bash
wrangler tail
```

