# Personal AI Employee - Silver Tier Runbook

This repository contains a local-first AI Employee implementation for Hackathon 0.

Current status:
- Silver-tier foundation with multiple watchers
- Human-in-the-loop approval flow
- Local email MCP server
- Scheduler + PM2 process management

## Architecture

Core loop:
1. Watchers detect events and create markdown action files in AI_Employee_Vault/Needs_Action.
2. Claude Code processes those items and creates plans or approval requests.
3. Human approves/rejects sensitive tasks via file movement.
4. Approval handler executes approved actions (MCP integration path) and archives to Done.

Main vault folders:
- AI_Employee_Vault/Inbox
- AI_Employee_Vault/Needs_Action
- AI_Employee_Vault/Pending_Approval
- AI_Employee_Vault/Approved
- AI_Employee_Vault/Rejected
- AI_Employee_Vault/Plans
- AI_Employee_Vault/Done
- AI_Employee_Vault/Logs

## Essential Files

Watchers and automation:
- scripts/base_watcher.py
- scripts/filesystem_watcher.py
- scripts/gmail_watcher.py
- scripts/whatsapp_watcher.py
- scripts/approval_handler.py
- scripts/approval_helper.py
- scripts/plan_generator.py
- scripts/schedule_tasks.py
- scripts/requirements.txt

MCP email server:
- mcp_servers/email_mcp/index.js
- mcp_servers/email_mcp/package.json
- mcp_servers/email_mcp/.env

PM2 configs:
- pm2/ecosystem.watchers.config.cjs
- pm2/ecosystem.scheduler.config.cjs
- pm2/PM2_SETUP.md

Project docs:
- CLAUDE.md
- Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md

## Prerequisites

- Python 3.12+
- Node.js + npm
- Claude Code
- Obsidian (for vault UX)

## Setup Commands

From repo root:

```powershell
Set-Location "D:\My Work\Hackathon-0"

# Python env + dependencies
py -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -U pip
& ".\.venv\Scripts\python.exe" -m pip install -r scripts\requirements.txt

# Playwright browser for WhatsApp watcher
& ".\.venv\Scripts\python.exe" -m playwright install chromium

# Node dependencies
npm install
Set-Location "mcp_servers\email_mcp"
npm install
Set-Location "..\.."
```

## Running Components (Manual)

Filesystem watcher:

```powershell
Set-Location "D:\My Work\Hackathon-0"
& ".\.venv\Scripts\python.exe" scripts\filesystem_watcher.py "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

Gmail watcher:

```powershell
Set-Location "D:\My Work\Hackathon-0"
& ".\.venv\Scripts\python.exe" scripts\gmail_watcher.py "D:\My Work\Hackathon-0\AI_Employee_Vault" "D:\My Work\Hackathon-0\credentials.json"
```

WhatsApp watcher (recommended for your current setup: headed continuous mode):

```powershell
Set-Location "D:\My Work\Hackathon-0"
& ".\.venv\Scripts\python.exe" scripts\whatsapp_watcher.py "D:\My Work\Hackathon-0\AI_Employee_Vault" "D:\My Work\Hackathon-0\scripts\.whatsapp_session" 45 false
```

WhatsApp onboarding only (single cycle):

```powershell
Set-Location "D:\My Work\Hackathon-0"
& ".\.venv\Scripts\python.exe" scripts\whatsapp_watcher.py "D:\My Work\Hackathon-0\AI_Employee_Vault" "D:\My Work\Hackathon-0\scripts\.whatsapp_session" 45 false 0 true
```

Approval handler:

```powershell
Set-Location "D:\My Work\Hackathon-0"
& ".\.venv\Scripts\python.exe" scripts\approval_handler.py "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

Scheduler:

```powershell
Set-Location "D:\My Work\Hackathon-0"
& ".\.venv\Scripts\python.exe" scripts\schedule_tasks.py "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

Email MCP server:

```powershell
Set-Location "D:\My Work\Hackathon-0\mcp_servers\email_mcp"
npm start
```

## Running with PM2 (Project-Local)

This repo uses local PM2 via npx (no global install required).

Install local PM2:

```powershell
Set-Location "D:\My Work\Hackathon-0"
npm install --save-dev pm2
```

Start watcher mode:

```powershell
Set-Location "D:\My Work\Hackathon-0"
npx pm2 startOrRestart pm2\ecosystem.watchers.config.cjs
npx pm2 save
```

Start scheduler mode (do not run with watcher mode at the same time):

```powershell
Set-Location "D:\My Work\Hackathon-0"
npx pm2 startOrRestart pm2\ecosystem.scheduler.config.cjs
npx pm2 save
```

Common PM2 commands:

```powershell
npx pm2 list
npx pm2 logs
npx pm2 logs whatsapp-watcher
npx pm2 restart whatsapp-watcher
npx pm2 stop all
npx pm2 delete all
```

## Human-in-the-Loop Commands

List pending approvals:

```powershell
Set-Location "D:\My Work\Hackathon-0\scripts"
& "..\.venv\Scripts\python.exe" approval_helper.py list "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

Approve an item:

```powershell
Set-Location "D:\My Work\Hackathon-0\scripts"
& "..\.venv\Scripts\python.exe" approval_helper.py approve "filename.md" "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

Reject an item:

```powershell
Set-Location "D:\My Work\Hackathon-0\scripts"
& "..\.venv\Scripts\python.exe" approval_helper.py reject "filename.md" "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

## End-to-End Flow

1. Input arrives:
- Files dropped in AI_Employee_Vault/Inbox
- New Gmail/WhatsApp unread activity

2. Watchers create action files:
- FILE_DROP_*.md
- GMAIL_*.md
- WHATSAPP_*.md

3. Claude processes Needs_Action:
- Create plans in AI_Employee_Vault/Plans for complex tasks
- Create approval files in AI_Employee_Vault/Pending_Approval for sensitive tasks

4. Human decision:
- Move file to AI_Employee_Vault/Approved or AI_Employee_Vault/Rejected

5. Approval handler processes decision:
- Executes approved action path
- Logs activity
- Moves processed file to AI_Employee_Vault/Done

## Claude Session

```powershell
Set-Location "D:\My Work\Hackathon-0\AI_Employee_Vault"
claude
```

Suggested prompt:

Process all pending files in /Needs_Action. Create plans for multi-step tasks, route sensitive actions to /Pending_Approval, and move completed work to /Done.

## Security Notes

- Sensitive runtime files are ignored in .gitignore.
- Keep credentials out of the vault markdown content.
- Use environment files for secrets in MCP services.
- Use approval flow for irreversible or risky actions.

## Troubleshooting

Watcher says 0 new unread while unread exists:
- Check watcher log summary fields: matched, already_processed, new.
- If needed for retest, run WhatsApp watcher with reprocess_existing=true.

WhatsApp session issues:
- Run onboarding mode once (non-headless) and complete session login.
- Ensure only one whatsapp_watcher.py process is running.

PM2 command not found:
- Use local PM2: npx pm2 ...

## Reference Documents

- CLAUDE.md
- Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md
