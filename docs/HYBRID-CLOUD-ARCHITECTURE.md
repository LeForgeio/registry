# Hybrid Cloud Architecture with LeForge

> Connect cloud workflows to on-premises resources securely using Cloudflare Tunnel

## The Problem

You have workflows running in the cloud (Nintex Workflow Cloud, Power Automate, etc.) but need to access:

- On-premises databases (SQL Server, Oracle, PostgreSQL)
- Internal REST APIs (ERP, CRM, custom apps)
- File shares (network drives, SharePoint on-prem)
- Active Directory for authentication

Traditional solutions require:
- VPN tunnels between cloud and on-prem
- Complex firewall rules
- Inbound ports opened to the internet
- Network configuration that IT security teams hate

## The Solution: LeForge + Cloudflare Tunnel

```
┌──────────────────────────────────────────────────────────────────────┐
│  CLOUD                                                                │
│                                                                       │
│  ┌─────────────────┐     ┌─────────────────┐     ┌────────────────┐  │
│  │ Nintex Workflow │     │ Power Automate  │     │ ServiceNow     │  │
│  │ Cloud           │     │                 │     │ Flow           │  │
│  │     │           │     │       │         │     │      │         │  │
│  └─────┼───────────┘     └───────┼─────────┘     └──────┼─────────┘  │
│        │                         │                      │            │
│        └─────────────────────────┼──────────────────────┘            │
│                                  │                                    │
│                                  ▼                                    │
│                     ┌────────────────────────┐                       │
│                     │  LeForge Xtension/     │                       │
│                     │  Connector/Action      │                       │
│                     └───────────┬────────────┘                       │
│                                 │ HTTPS                              │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │
                    ╔═════════════╧═════════════╗
                    ║   Cloudflare Edge         ║
                    ║   app.leforge.io          ║
                    ║   ┌──────────────────┐    ║
                    ║   │ Zero Trust       │    ║
                    ║   │ Access Policies  │    ║
                    ║   └──────────────────┘    ║
                    ╚═════════════╤═════════════╝
                                  │
                                  │ Cloudflare Tunnel
                                  │ (outbound only, encrypted)
                                  │
┌─────────────────────────────────┼────────────────────────────────────┐
│  ON-PREMISES                    │                                    │
│                                 ▼                                    │
│                    ┌────────────────────────┐                       │
│                    │   cloudflared          │◄── No inbound ports!  │
│                    │   (tunnel client)      │                       │
│                    └───────────┬────────────┘                       │
│                                │                                     │
│                                ▼                                     │
│                    ┌────────────────────────┐                       │
│                    │   LeForge              │                       │
│                    │   ┌──────────────────┐ │                       │
│                    │   │ onprem-connector │ │                       │
│                    │   │ plugin           │ │                       │
│                    │   └────────┬─────────┘ │                       │
│                    └────────────┼───────────┘                       │
│                                 │                                    │
│      ┌──────────────────────────┼──────────────────────────┐        │
│      │                          │                          │        │
│      ▼                          ▼                          ▼        │
│ ┌──────────┐            ┌──────────────┐           ┌────────────┐   │
│ │ Database │            │ Internal API │           │ File Share │   │
│ │ Server   │            │ Server       │           │            │   │
│ └──────────┘            └──────────────┘           └────────────┘   │
│                                                                      │
│                    🏢 Corporate Network                              │
└──────────────────────────────────────────────────────────────────────┘
```

## Security Benefits

| Feature              | Description                                        |
| -------------------- | -------------------------------------------------- |
| No inbound ports     | Tunnel makes outbound connections only             |
| Zero Trust           | Cloudflare Access validates every request          |
| Encryption           | TLS 1.3 from cloud to on-prem                      |
| Audit logging        | Full request trail in LeForge and Cloudflare       |
| Credential isolation | Database passwords never leave on-prem environment |
| DDoS protection      | Cloudflare edge absorbs attacks                    |

## Step-by-Step Setup

> **📘 Complete Setup Guide:** For detailed instructions including Cloudflare account setup, domain configuration, and troubleshooting, see [CLOUDFLARE-TUNNEL-SETUP.md](./CLOUDFLARE-TUNNEL-SETUP.md)

### 1. Create Cloudflare Tunnel

1. Log into [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com)
2. Navigate to **Networks** → **Tunnels** → **Create a tunnel**
3. Name your tunnel (e.g., `leforge-production`)
4. Copy the tunnel token for the next step

### 2. Deploy LeForge + Cloudflared

```yaml
# docker-compose.yml
version: '3.8'

services:
  leforge:
    image: leforge/leforge:latest
    container_name: leforge-app
    environment:
      - NODE_ENV=production
      - LEFORGE_SECURE_COOKIES=false  # If using HTTP internally
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

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - leforge-network
    depends_on:
      leforge:
        condition: service_healthy

networks:
  leforge-network:
    driver: bridge

volumes:
  leforge-postgres-data:
  leforge-plugin-data:
```

### 3. Configure Cloudflare Dashboard

1. Go to **Zero Trust** → **Networks** → **Tunnels**
2. Select your tunnel → **Configure**
3. Add public hostname:
   - Subdomain: `app`
   - Domain: `yourdomain.com`
   - Service: `http://leforge-app:4000`

### 4. Add Access Policies (Recommended)

1. Go to **Zero Trust** → **Access** → **Applications**
2. Add application:
   - Application domain: `app.yourdomain.com`
   - Session duration: 24 hours
3. Add policy:
   - For workflows: **Service Auth** (use service tokens)
   - For users: **Identity provider** (Azure AD, Okta, etc.)

### 5. Configure LeForge Connections

In LeForge UI, add connections for your on-prem resources:

**Database Connection:**
```json
{
  "id": "prod-sql",
  "name": "Production SQL Server",
  "type": "database",
  "config": {
    "driver": "mssql",
    "host": "sql01.corp.local",
    "port": 1433,
    "database": "ProductionDB",
    "options": {
      "encrypt": true,
      "trustServerCertificate": true
    }
  }
}
```

**Internal API Connection:**
```json
{
  "id": "internal-erp",
  "name": "SAP ERP API",
  "type": "api",
  "config": {
    "baseUrl": "https://erp.corp.local/api",
    "auth": {
      "type": "basic",
      "username": "api_user"
    }
  }
}
```

### 6. Install Platform Integration

**For Nintex Workflow Cloud:**

1. Download `onprem-connector.xtension.json` from this repo
2. Go to Nintex Admin → Xtensions → Add
3. Upload JSON file
4. Configure connection:
   - URL: `https://app.yourdomain.com/api/v1`
   - Auth: Bearer token (your LeForge API key)

**For Power Automate:**

1. Download `apiDefinition.swagger.json`
2. Go to Power Automate → Custom Connectors → New
3. Import from OpenAPI file
4. Configure authentication

## Usage Example: Nintex Workflow Cloud

### Scenario: Approval workflow needs customer data from on-prem database

```
┌─────────────────────────────────────────────────────────────────┐
│  Nintex Workflow Cloud                                          │
│                                                                 │
│  1. Form submitted                                              │
│              │                                                  │
│              ▼                                                  │
│  2. ┌─────────────────────────────┐                            │
│     │ LeForge: Query On-Prem DB   │                            │
│     │ Connection: prod-sql        │                            │
│     │ Query: SELECT * FROM        │                            │
│     │   Customers WHERE           │                            │
│     │   ID = {{form.customerId}}  │────────────────────────┐   │
│     └─────────────────────────────┘                        │   │
│                                                            │   │
│  3. ┌─────────────────────────────┐◄───────────────────────┘   │
│     │ Customer Data returned:     │                            │
│     │ - Name: Acme Corp           │                            │
│     │ - Credit: $50,000           │                            │
│     │ - Region: West              │                            │
│     └─────────────────────────────┘                            │
│              │                                                  │
│              ▼                                                  │
│  4. Branch based on credit limit                               │
│              │                                                  │
│              ▼                                                  │
│  5. Route to appropriate approver                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Workflow Actions

**Step 2: Query Database**
```
Action: Query On-Prem Database
Connection: prod-sql
Query: SELECT CustomerName, CreditLimit, Region, AccountManager 
       FROM Customers 
       WHERE CustomerID = @id
Parameters:
  - id: {{FormData.customerId}}
Output: {{CustomerData}}
```

**Step 4: Decision Branch**
```
Condition: {{CustomerData.CreditLimit}} > 100000
  True → Senior Manager Approval
  False → Manager Approval
```

## Troubleshooting

### Tunnel Not Connected

```bash
# Check tunnel status in Cloudflare dashboard
# Or via CLI:
cloudflared tunnel info leforge-tunnel

# Check cloudflared container logs
docker logs cloudflared
```

### LeForge Can't Reach Database

```bash
# Verify network connectivity from LeForge container
docker exec leforge-app ping sql01.corp.local

# Test port connectivity
docker exec leforge-app nc -zv sql01.corp.local 1433

# Check DNS resolution
docker exec leforge-app nslookup sql01.corp.local
```

### Authentication Errors

1. Verify API key is correct in connector config
2. Check Cloudflare Access policies allow service auth
3. Verify database credentials in LeForge connection

## Best Practices

1. **Use connection IDs, not direct strings** - Store credentials in LeForge, reference by ID
2. **Create dedicated service accounts** - Don't use personal credentials
3. **Apply least privilege** - Grant minimum permissions needed
4. **Enable audit logging** - Track all on-prem access
5. **Use parameterized queries** - Prevent SQL injection
6. **Set appropriate timeouts** - On-prem resources may be slower
7. **Implement retry logic** - Handle transient failures
8. **Monitor tunnel health** - Alert on disconnections

## Related Documentation

- [On-Prem Connector Plugin](../plugins/onprem-connector/)
- [Nintex Cloud Xtension](../integrations/nintex-cloud/)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Access Docs](https://developers.cloudflare.com/cloudflare-one/policies/access/)
