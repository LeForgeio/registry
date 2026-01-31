# Cloudflare Tunnel Setup Guide

> Complete step-by-step guide to connect LeForge to the internet securely using Cloudflare Tunnel

## Overview

Cloudflare Tunnel creates a secure outbound-only connection from your on-premises LeForge instance to Cloudflare's edge network. This allows external services (Nintex, Power Automate, etc.) to reach your LeForge instance without:

- Opening inbound firewall ports
- Configuring VPNs
- Exposing your server directly to the internet

```
Your LeForge Server ──(outbound)──> Cloudflare Edge <──(HTTPS)── Cloud Platforms

No inbound connections required!
```

## Prerequisites

Before starting, you'll need:

- [ ] A Cloudflare account (free tier works)
- [ ] A domain name added to Cloudflare (can be a new or existing domain)
- [ ] LeForge running on a server (Docker or bare metal)
- [ ] Ability to run `cloudflared` on the same network as LeForge

## Part 1: Cloudflare Account & Domain Setup

### Step 1.1: Create Cloudflare Account

1. Go to [cloudflare.com](https://cloudflare.com) and click **Sign Up**
2. Enter your email and create a password
3. Verify your email address

### Step 1.2: Add Your Domain to Cloudflare

You have two options:

**Option A: Use your own domain**
1. In Cloudflare dashboard, click **Add a Site**
2. Enter your domain name (e.g., `yourcompany.com`)
3. Select the **Free** plan (sufficient for tunnels)
4. Cloudflare will scan your DNS records
5. Update your domain's nameservers at your registrar to Cloudflare's nameservers
6. Wait for DNS propagation (usually 5-30 minutes)

**Option B: Buy a domain through Cloudflare**
1. Go to **Domain Registration** → **Register Domains**
2. Search for and purchase a domain
3. It's automatically configured with Cloudflare

### Step 1.3: Choose Your Subdomain

Decide what URL you want for your LeForge instance:

| Your Domain | Subdomain | Full URL |
|-------------|-----------|----------|
| `acmecorp.com` | `leforge` | `leforge.acmecorp.com` |
| `acmecorp.com` | `automation` | `automation.acmecorp.com` |
| `internal-tools.io` | `app` | `app.internal-tools.io` |
| `mycompany.net` | `forge` | `forge.mycompany.net` |

**Note:** You'll configure this subdomain in Part 3.

---

## Part 2: Install cloudflared

`cloudflared` is the tunnel client that runs alongside LeForge.

### Windows

```powershell
# Option 1: Using winget (recommended)
winget install Cloudflare.cloudflared

# Option 2: Direct download
# Download from: https://github.com/cloudflare/cloudflared/releases/latest
# Get: cloudflared-windows-amd64.msi
```

### macOS

```bash
brew install cloudflared
```

### Linux (Debian/Ubuntu)

```bash
# Download the package
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install
sudo dpkg -i cloudflared.deb

# Verify
cloudflared --version
```

### Linux (RHEL/CentOS)

```bash
curl -L --output cloudflared.rpm https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
sudo rpm -i cloudflared.rpm
```

### Docker

```bash
docker pull cloudflare/cloudflared:latest
```

---

## Part 3: Create the Tunnel

You can create tunnels via the **Cloudflare Dashboard** (easier) or **CLI** (more control).

### Method A: Dashboard (Recommended for Beginners)

1. Log into [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com)
   - First time? You'll be prompted to set up Zero Trust (free plan available)

2. Navigate to **Networks** → **Tunnels**

3. Click **Create a tunnel**

4. Select **Cloudflared** as the connector type

5. **Name your tunnel**
   - Use something descriptive like `leforge-production` or `acme-leforge`
   - Click **Save tunnel**

6. **Install and run connector**
   - Cloudflare will show you a command with a unique token
   - Copy this token - you'll need it later
   - Example token: `eyJhIjoiNDdkYWFjOGZiNGI1M2E2NThmMz...`

7. **Add public hostname**
   - Subdomain: Enter your chosen subdomain (e.g., `leforge`)
   - Domain: Select your domain from dropdown
   - Path: Leave empty
   - Service Type: `HTTP`
   - URL: `localhost:4000` (or `leforge-app:4000` if using Docker networking)

8. Click **Save tunnel**

### Method B: CLI

```bash
# Step 1: Authenticate (opens browser)
cloudflared tunnel login

# Step 2: Create tunnel (saves credentials to ~/.cloudflared/)
cloudflared tunnel create leforge-tunnel

# Note the Tunnel ID from the output, e.g.:
# Created tunnel leforge-tunnel with id abc12345-1234-5678-abcd-1234567890ab

# Step 3: Create config file
```

Create `~/.cloudflared/config.yml`:

```yaml
# Replace YOUR_TUNNEL_ID with your actual tunnel ID
tunnel: YOUR_TUNNEL_ID
credentials-file: /root/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  # Replace with your subdomain and domain
  - hostname: leforge.yourcompany.com
    service: http://localhost:4000
  # Catch-all rule (required)
  - service: http_status:404
```

```bash
# Step 4: Route DNS (creates the subdomain)
cloudflared tunnel route dns leforge-tunnel leforge.yourcompany.com

# Step 5: Test the tunnel
cloudflared tunnel run leforge-tunnel
```

---

## Part 4: Run cloudflared with LeForge

Choose the deployment method that matches your LeForge setup.

### Option A: Docker Compose (Recommended)

Add `cloudflared` to your existing LeForge `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Your existing LeForge service
  leforge-app:
    image: leforge/leforge:latest
    container_name: leforge-app
    ports:
      - "4000:4000"  # Optional: only needed for local access
    environment:
      - NODE_ENV=production
      # IMPORTANT: Set to false when using reverse proxy
      - LEFORGE_SECURE_COOKIES=false
    volumes:
      - leforge-postgres-data:/var/lib/postgresql/data
      - leforge-plugin-data:/app/data/plugins
    networks:
      - leforge-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Cloudflare Tunnel
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    command: tunnel run
    environment:
      # Get this from Cloudflare Dashboard → Tunnels → Your Tunnel → Configure
      - TUNNEL_TOKEN=YOUR_TUNNEL_TOKEN_HERE
    networks:
      - leforge-network
    depends_on:
      leforge-app:
        condition: service_healthy
    restart: unless-stopped

networks:
  leforge-network:
    driver: bridge

volumes:
  leforge-postgres-data:
  leforge-plugin-data:
```

**Important:** In the Cloudflare Dashboard, set the service URL to `http://leforge-app:4000` (using the Docker container name, not `localhost`).

Start the stack:

```bash
docker compose up -d
```

### Option B: Standalone cloudflared Service

If LeForge runs directly on the host (not in Docker):

```bash
# Install as a system service
sudo cloudflared service install YOUR_TUNNEL_TOKEN

# Start the service
sudo systemctl start cloudflared

# Enable auto-start on boot
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

### Option C: Windows Service

```powershell
# Run as Administrator
cloudflared service install YOUR_TUNNEL_TOKEN

# Start the service
Start-Service cloudflared

# Verify it's running
Get-Service cloudflared
```

---

## Part 5: Verify the Connection

### Check Tunnel Status in Dashboard

1. Go to **Zero Trust** → **Networks** → **Tunnels**
2. Your tunnel should show **HEALTHY** status with a green indicator
3. Click the tunnel name to see connector details

### Test External Access

From any device outside your network:

```bash
# Replace with your actual URL
curl https://leforge.yourcompany.com/api/v1/health

# Expected response:
# {"status":"ok","timestamp":"2026-01-30T..."}
```

### Test from Browser

1. Open `https://leforge.yourcompany.com` in your browser
2. You should see the LeForge login page
3. Log in with your credentials

---

## Part 6: Configure Security (Recommended)

### Enable Cloudflare Access (Zero Trust)

Cloudflare Access adds authentication before traffic reaches LeForge.

1. Go to **Zero Trust** → **Access** → **Applications**

2. Click **Add an application**

3. Select **Self-hosted**

4. Configure the application:
   - **Application name:** LeForge
   - **Session duration:** 24 hours
   - **Application domain:** `leforge.yourcompany.com`

5. **Add a policy:**

   **For Interactive Users:**
   - Policy name: `Allow Employees`
   - Action: `Allow`
   - Include rule: `Emails ending in @yourcompany.com`
   
   **For API Access (Workflows):**
   - Policy name: `Service Auth`
   - Action: `Service Auth`
   - Include rule: `Service Token`

6. Click **Save**

### Create Service Token for Workflows

For Nintex, Power Automate, etc. to authenticate:

1. Go to **Zero Trust** → **Access** → **Service Auth** → **Service Tokens**
2. Click **Create Service Token**
3. Name it (e.g., `Nintex Production`)
4. Copy both:
   - `CF-Access-Client-Id`
   - `CF-Access-Client-Secret`
5. Configure these headers in your workflow connectors

---

## Part 7: Configure Your Workflow Platform

### Nintex Workflow Cloud

1. Download the LeForge Xtension from the registry
2. In Nintex Admin → **Xtensions** → **Add custom connector**
3. Upload the Xtension JSON
4. Configure connection:
   - **Base URL:** `https://leforge.yourcompany.com/api/v1`
   - **Authentication:** Bearer Token
   - **Token:** Your LeForge API key
   - **Additional Headers:**
     - `CF-Access-Client-Id: YOUR_SERVICE_TOKEN_ID`
     - `CF-Access-Client-Secret: YOUR_SERVICE_TOKEN_SECRET`

### Power Automate

1. Go to **Custom connectors** → **New custom connector**
2. Import the OpenAPI spec from LeForge
3. Update the host to `leforge.yourcompany.com`
4. Configure authentication with your service token headers

### n8n

1. Add an HTTP Request node
2. Set URL to `https://leforge.yourcompany.com/api/v1/your-endpoint`
3. Add headers:
   - `Authorization: Bearer YOUR_API_KEY`
   - `CF-Access-Client-Id: YOUR_SERVICE_TOKEN_ID`
   - `CF-Access-Client-Secret: YOUR_SERVICE_TOKEN_SECRET`

---

## Troubleshooting

### Tunnel Shows "Inactive" or "Down"

```bash
# Check cloudflared logs
docker logs cloudflared

# Or for system service
sudo journalctl -u cloudflared -f
```

Common causes:
- Invalid or expired tunnel token
- Network blocking outbound connections to Cloudflare
- cloudflared not running

### "502 Bad Gateway" Error

The tunnel is working, but can't reach LeForge:

1. Verify LeForge is running:
   ```bash
   docker ps | grep leforge
   curl http://localhost:4000/api/v1/health
   ```

2. Check the service URL in Cloudflare Dashboard matches your setup:
   - Docker: `http://leforge-app:4000`
   - Direct: `http://localhost:4000`

3. Verify Docker network connectivity:
   ```bash
   docker exec cloudflared wget -qO- http://leforge-app:4000/api/v1/health
   ```

### "Access Denied" or "403 Forbidden"

If using Cloudflare Access:
1. Verify you're logged in or using correct service token
2. Check Access policy allows your identity/token
3. Verify service token headers are being sent correctly

### SSL/Certificate Errors

1. Ensure your domain's SSL/TLS mode is set to **Full** in Cloudflare:
   - Dashboard → Your domain → **SSL/TLS** → **Full**

2. If LeForge runs on HTTPS internally, set tunnel service to `https://...`

### Cookie/Session Issues

If you can't stay logged in:

1. Set `LEFORGE_SECURE_COOKIES=false` in LeForge environment variables
2. Ensure your browser accepts cookies from your domain
3. Check that the domain matches exactly (no www mismatch)

---

## Reference: Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TUNNEL_TOKEN` | Yes | Token from Cloudflare Dashboard |
| `TUNNEL_LOGLEVEL` | No | `debug`, `info`, `warn`, `error` |
| `TUNNEL_TRANSPORT_PROTOCOL` | No | `auto`, `http2`, `quic` |

---

## Reference: Firewall Requirements

cloudflared only needs **outbound** connectivity:

| Destination | Port | Protocol | Purpose |
|-------------|------|----------|---------|
| `*.cloudflare.com` | 443 | TCP | API and tunnel |
| `*.argotunnel.com` | 7844 | UDP/TCP | Tunnel traffic |

No inbound ports required!

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR LEFORGE SETUP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Public URL:    https://________________.________________       │
│                         (subdomain)        (domain)             │
│                                                                 │
│  Tunnel Name:   ________________________________________        │
│                                                                 │
│  Tunnel Token:  eyJ... (stored in docker-compose.yml)          │
│                                                                 │
│  LeForge Port:  4000 (internal)                                │
│                                                                 │
│  Service URL:   http://leforge-app:4000 (in Cloudflare)        │
│                                                                 │
│  API Key:       LF___________________ (for workflows)          │
│                                                                 │
│  Service Token ID: _________________________ (Cloudflare)      │
│                                                                 │
│  Service Token Secret: _____________________ (Cloudflare)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Add on-premises connections** - Configure database, API, and file share access in LeForge
2. **Build your first workflow** - Create a Nintex or Power Automate workflow that calls LeForge
3. **Review security** - Enable Cloudflare Access and audit logging
4. **Monitor** - Set up alerts for tunnel disconnections

## Related Documentation

- [Hybrid Cloud Architecture](./HYBRID-CLOUD-ARCHITECTURE.md)
- [On-Prem Connector Plugin](../plugins/onprem-connector/)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Zero Trust](https://developers.cloudflare.com/cloudflare-one/)
