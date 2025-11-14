# ImageViewer Cloudflare Worker

This directory contains the Cloudflare Worker configuration for serving remote install scripts for ImageViewer.

## Setup

1. Install Wrangler CLI:
   ```bash
   npm install -g wrangler
   ```

2. Authenticate with Cloudflare:
   ```bash
   wrangler auth login
   ```

3. Deploy the worker:
   ```bash
   wrangler deploy
   ```

## Configuration

Edit `wrangler.toml` to configure:
- Worker name
- Custom domain routes (optional)
- Environment variables

## Usage

Once deployed, users can install ImageViewer with:

```bash
# Linux/macOS
curl -fsSL https://imageviewer-installer.yourdomain.com/install.sh | bash

# Windows PowerShell
irm https://imageviewer-installer.yourdomain.com/install.ps1 | iex
```

## Endpoints

- `/` or `/install.sh` - Bash install script for Linux/macOS
- `/install.ps1` - PowerShell install script for Windows
- `/health` - Health check endpoint

## Development

Run locally:
```bash
wrangler dev
```
