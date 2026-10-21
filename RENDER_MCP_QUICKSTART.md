# Render MCP Server - Quick Start

## ✅ Configuration Complete!

The Render MCP server has been configured and is ready to use.

**Configuration file location:**
```
C:\Users\ElsieSetladi\.kiro\settings\mcp.json
```

---

## Next Steps

### 1. Restart Kiro (Important!)

The MCP server configuration will be loaded when Kiro restarts.

**How to restart:**
- Close this session
- Reopen Kiro
- Or reload window: `Ctrl+Shift+P` → "Reload Window"

### 2. First Time: Set Your Workspace

When you first use Render commands, you'll need to:

```
Set my Render workspace to [YOUR_WORKSPACE_NAME]
```

**To find your workspace name:**
- Go to https://dashboard.render.com
- Your workspace name is shown in the dashboard

### 3. Authorize Access (OAuth)

The first Render command will trigger OAuth authorization:
1. Browser window will open automatically
2. Log in to your Render account
3. Grant permissions
4. Return to Kiro

---

## Quick Test Commands

After restart and authorization, try these:

```
List my Render workspaces
```

```
List my Render services
```

```
Show details of [service-name]
```

---

## Common Commands for Your TDIS App

### Deploy Your Application

```
Create a new web service called tdis-backend using https://github.com/[your-repo]
```

```
Deploy the tdis-backend service on Render
```

### Database Management

```
Create a new database named tdis-db with 10 GB storage
```

```
List all my Render databases
```

### Monitoring

```
Show recent logs for tdis-backend
```

```
What was the CPU usage for tdis-backend today?
```

### Environment Variables

```
Show environment variables for tdis-backend
```

```
Update SECRET_KEY to "new-value" for tdis-backend
```

---

## Troubleshooting

### Commands not working?
→ Make sure you **restarted Kiro** after adding the configuration

### "Workspace not set"?
→ Run: `Set my Render workspace to [your-workspace-name]`

### Authorization failed?
→ Check you're logged into the correct Render account in your browser

---

## Configuration Details

```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com",
      "transport": {
        "type": "sse"
      },
      "auth": {
        "type": "oauth"
      }
    }
  }
}
```

**Server URL:** https://mcp.render.com
**Authentication:** OAuth (automatic on first use)
**Transport:** Server-Sent Events (SSE)

---

## Resources

- **Render Dashboard:** https://dashboard.render.com
- **Documentation:** https://render.com/docs/mcp-server
- **API Docs:** https://api-docs.render.com
- **GitHub:** https://github.com/render-oss/render-mcp-server

---

## Ready to Deploy Your TDIS App?

Once the MCP server is working, you can deploy your application with commands like:

1. **Create PostgreSQL database:**
   ```
   Create a new Render database named tdis-production-db with 10 GB storage
   ```

2. **Create Redis instance:**
   ```
   Create a new Render Key Value instance named tdis-redis
   ```

3. **Deploy backend:**
   ```
   Create a web service named tdis-backend using https://github.com/[your-repo]
   ```

4. **Deploy frontend:**
   ```
   Create a static site named tdis-frontend using https://github.com/[your-repo]/frontend
   ```

---

**Status:** ✅ Configured  
**Next:** Restart Kiro  
**Then:** `List my Render workspaces`
