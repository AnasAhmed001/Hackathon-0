---
name: ai-vault-watcher-operations
description: |
  Watcher lifecycle and health skill for starting, stopping, validating,
  and recovering Gmail and filesystem watchers with safe operational checks.
---

# Watcher Operations

Use this skill to operate watcher processes reliably.

## Scope

- scripts/gmail_watcher.py
- scripts/filesystem_watcher.py
- scripts/watcher.log

## When To Use

- Initial startup of watcher services
- Verifying watcher health after config changes
- Recovering from crashes or stale processes
- Confirming watchers are writing to AI_Employee_Vault/Needs_Action

## Startup Commands (Windows)

From repository root:

```powershell
Set-Location scripts
py -m pip install -r requirements.txt
py filesystem_watcher.py "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

For Gmail watcher:

```powershell
Set-Location scripts
py gmail_watcher.py "..\AI_Employee_Vault" "..\credentials.json"
```

## Health Checks

1. Process-level checks:
   - Confirm watcher process is running
   - Confirm no duplicate competing processes
2. Functional checks:
   - New inbox drop creates a matching Needs_Action artifact
   - New important email appears in Needs_Action
3. Log checks:
   - Tail scripts/watcher.log for recent errors and stack traces

## Recovery Procedure

1. Stop the failing watcher process.
2. Inspect scripts/watcher.log for root cause.
3. Fix configuration or dependency issue.
4. Restart watcher.
5. Validate with one controlled test event.

## Scheduling Guidance

Use Task Scheduler for periodic starts or persistent supervisors for long-running behavior.

## PM2 Guidance (Preferred)

Use PM2 configs in the pm2 directory:

- pm2/ecosystem.watchers.config.cjs: long-running watcher mode
- pm2/ecosystem.scheduler.config.cjs: scheduler mode

Core commands:

```powershell
Set-Location "D:\My Work\Hackathon-0"
New-Item -ItemType Directory -Force -Path "scripts\\logs" | Out-Null
pm2 start pm2\\ecosystem.watchers.config.cjs
pm2 save
pm2 list
pm2 logs
```

Do not run watcher mode and scheduler mode at the same time.

## Safety Rules

- Never delete Needs_Action artifacts during recovery.
- Do not run multiple instances of the same watcher unless explicitly intended.
- Treat credentials and tokens as secrets; never place them in AI_Employee_Vault.

## Operational Output Contract

When running this skill, report:

- Which watcher(s) were started/stopped
- Current health status per watcher
- Last observed successful event time
- Any blocking errors and next action
