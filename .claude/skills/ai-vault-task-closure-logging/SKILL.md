---
name: ai-vault-task-closure-logging
description: |
  Completion and audit skill for moving finished artifacts to Done,
  updating Dashboard summaries, and writing structured logs.
---

# Task Closure And Logging

Use this skill when a task or approval cycle is complete.

## Folder Moves

On successful completion:

- Move source from AI_Employee_Vault/Needs_Action to AI_Employee_Vault/Done
- Move related plan from AI_Employee_Vault/Plans to AI_Employee_Vault/Done
- Move approval file from AI_Employee_Vault/Approved to AI_Employee_Vault/Done

On rejection:

- Keep source task traceable
- Move rejection artifact to AI_Employee_Vault/Done after closure note

## Audit Log Format

Store logs in AI_Employee_Vault/Logs with JSON-compatible entries containing:

- timestamp
- action_type
- actor
- target
- parameters
- approval_status
- result

## Dashboard Update

Append concise recent activity items in AI_Employee_Vault/Dashboard.md.

## Safety Rules

- Do not mark done if action did not execute successfully.
- Preserve end-to-end traceability between source, plan, approval, and result.
