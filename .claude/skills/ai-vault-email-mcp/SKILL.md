---
name: ai-vault-email-mcp
description: |
  Email execution skill for the local email MCP server in
  mcp_servers/email_mcp. Sends approved emails via SMTP
  and supports dry-run testing.
---

# Email MCP Execution

Use this skill when an email action is approved and ready to execute.

## Server Assumptions

- MCP config in .claude/mcp.json
- Email server command points to mcp_servers/email_mcp/index.js
- Env vars:
  - GMAIL_EMAIL
  - GMAIL_APP_PASSWORD
  - DRY_RUN (optional)

## Tool Contract

- Tool name: send-email
- Inputs:
  - to
  - subject
  - text
  - html (optional)

## Execution Procedure

1. Confirm corresponding approval file is in AI_Employee_Vault/Approved.
2. Validate recipient and subject against approval details.
3. Call MCP tool send-email with approved parameters only.
4. Capture response payload (success, messageId, errors).
5. Write/update audit entry in AI_Employee_Vault/Logs.

## Dry Run Guidance

- During testing, set DRY_RUN=true.
- Expect preview output and no real email delivery.

## Safety Rules

- Never send without approval for sensitive cases.
- Never alter approved parameters without new approval.
- If MCP call fails, do not retry blindly; record failure and escalate.
