# On-Premises Connector

> Secure gateway from cloud workflows to on-premises resources via Cloudflare Tunnel

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CLOUD (Nintex Workflow Cloud, Power Automate, etc.)                    │
│                                                                         │
│  ┌───────────────────────┐                                              │
│  │  Your Workflow        │                                              │
│  │  ┌─────────────────┐  │         HTTPS                               │
│  │  │ LeForge Xtension├──┼────────────────────┐                        │
│  │  └─────────────────┘  │                    │                        │
│  └───────────────────────┘                    │                        │
└───────────────────────────────────────────────┼────────────────────────┘
                                                │
                                                ▼
                              ┌─────────────────────────────┐
                              │   Cloudflare Edge           │
                              │   • DDoS protection         │
                              │   • WAF rules               │
                              │   • Access policies         │
                              └──────────┬──────────────────┘
                                         │ Tunnel (encrypted)
                                         │ (outbound only!)
┌────────────────────────────────────────┼────────────────────────────────┐
│  YOUR ON-PREMISES NETWORK              │                                │
│                                        ▼                                │
│                         ┌──────────────────────────┐                    │
│                         │   cloudflared            │                    │
│                         │   (no inbound ports)     │                    │
│                         └────────────┬─────────────┘                    │
│                                      │                                  │
│                                      ▼                                  │
│                         ┌──────────────────────────┐                    │
│                         │   LeForge                │                    │
│                         │   + onprem-connector     │                    │
│                         └────────────┬─────────────┘                    │
│                                      │                                  │
│        ┌─────────────────────────────┼─────────────────────────┐       │
│        │                             │                         │       │
│        ▼                             ▼                         ▼       │
│  ┌───────────┐              ┌───────────────┐          ┌────────────┐  │
│  │ SQL Server│              │ Internal APIs │          │File Shares │  │
│  │ Oracle    │              │ ERP, CRM, etc │          │SharePoint  │  │
│  │ PostgreSQL│              │               │          │            │  │
│  └───────────┘              └───────────────┘          └────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Why This Pattern?

| Challenge | Traditional VPN | Cloudflare Tunnel + LeForge |
|-----------|----------------|----------------------------|
| Firewall rules | Inbound ports required | No inbound ports |
| Network complexity | Site-to-site VPN setup | Single outbound connection |
| Security | VPN credentials to manage | Zero Trust, per-request auth |
| Audit trail | Limited visibility | Full request logging |
| Scalability | VPN capacity limits | Cloudflare global edge |

## Supported Backends

### Databases
- SQL Server (2016+)
- PostgreSQL (10+)
- MySQL / MariaDB
- Oracle (12c+)

### APIs
- Internal REST APIs
- SOAP services (via REST wrapper)
- GraphQL endpoints

### File Systems
- Windows file shares (SMB/CIFS)
- NFS mounts
- SharePoint on-premises

### Directory Services
- Active Directory
- LDAP

## Setup Guide

### Step 1: Deploy LeForge with Cloudflare Tunnel

```yaml
# docker-compose.yml
services:
  leforge:
    image: leforge/leforge:latest
    container_name: leforge-app
    environment:
      - NODE_ENV=production
    volumes:
      - leforge-data:/app/data
    networks:
      - leforge-network

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=your_tunnel_token
    networks:
      - leforge-network
    depends_on:
      - leforge

networks:
  leforge-network:

volumes:
  leforge-data:
```

### Step 2: Configure Tunnel in Cloudflare Dashboard

1. Go to Cloudflare Zero Trust → Networks → Tunnels
2. Create tunnel or use existing
3. Add public hostname:
   - **Subdomain**: `app` (or your choice)
   - **Domain**: `leforge.io` (your domain)
   - **Service**: `http://leforge-app:4000`

### Step 3: Add Access Policies (Recommended)

1. Go to Cloudflare Zero Trust → Access → Applications
2. Add application for `app.leforge.io`
3. Configure policies:
   - Service Auth (for Nintex Workflow Cloud)
   - Or specific IP ranges
   - Or identity provider authentication

### Step 4: Configure Connections in LeForge

In LeForge UI → Settings → Connections:

```json
{
  "id": "my-sql-server",
  "name": "Production SQL Server",
  "type": "database",
  "config": {
    "type": "mssql",
    "host": "sql01.internal.corp",
    "port": 1433,
    "database": "ProductionDB",
    "encrypt": true
  },
  "credentials": {
    "username": "leforge_svc",
    "password": "encrypted:..."
  }
}
```

### Step 5: Install Nintex Workflow Cloud Xtension

1. Download `onprem-connector.xtension.json`
2. In Nintex Workflow Cloud → Xtensions → Add
3. Upload the JSON file
4. Configure connection with your LeForge URL and API key

## Usage Examples

### Query SQL Server from Nintex Workflow

```
Action: Query On-Prem Database
Connection: my-sql-server
Query: SELECT * FROM Orders WHERE Status = @status AND Region = @region
Parameters:
  - status: Pending
  - region: {{workflow.region}}
```

### Call Internal API

```
Action: Call Internal API
Connection: internal-erp
Endpoint: /api/v1/customers/{{customerId}}
Method: GET
```

### Read File from Network Share

```
Action: Read File from Share
Connection: shared-drive
Path: /reports/{{year}}/{{month}}/summary.xlsx
Encoding: base64
```

### Authenticate User Against AD

```
Action: Authenticate with Active Directory
Connection: corp-ad
Username: {{form.username}}
Password: {{form.password}}
```

## Security Considerations

### Network Security
- Cloudflare Tunnel uses outbound-only connections
- No inbound firewall rules required
- All traffic encrypted with TLS 1.3

### Authentication Layers
1. **Cloudflare Access** - Zero Trust policies at the edge
2. **LeForge API Key** - Application-level authentication
3. **Connection Credentials** - Per-resource authentication

### Data Protection
- Connection credentials encrypted at rest
- Parameterized queries prevent SQL injection
- Path validation prevents directory traversal
- Audit logging for all requests

### Least Privilege
- Create dedicated service accounts for LeForge
- Grant minimum required permissions
- Use read-only connections where possible

## Troubleshooting

### Connection Test Fails

```bash
# Check tunnel status
docker logs cloudflared

# Verify LeForge can reach database
docker exec leforge-app ping sql01.internal.corp

# Test from LeForge container
docker exec -it leforge-app nc -zv sql01.internal.corp 1433
```

### Timeout Errors

- Increase timeout in plugin config
- Check network latency to on-prem resource
- Verify firewall rules between LeForge and resource

### Authentication Errors

- Verify service account credentials
- Check if account is locked or expired
- Ensure proper permissions on target resource

## API Reference

| Endpoint | Description |
|----------|-------------|
| `POST /queryDatabase` | Execute SQL query |
| `POST /executeStoredProcedure` | Run stored procedure |
| `POST /callInternalApi` | Proxy to internal API |
| `POST /listFiles` | List files in share |
| `POST /readFile` | Read file content |
| `POST /writeFile` | Write file to share |
| `POST /ldapSearch` | Search Active Directory |
| `POST /ldapAuthenticate` | Verify AD credentials |

## License

MIT
