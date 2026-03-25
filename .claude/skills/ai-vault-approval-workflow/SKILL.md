---
name: ai-vault-approval-workflow
description: |
  Human-in-the-loop workflow skill for creating, validating, and
  tracking approval files across Pending_Approval, Approved, and
  Rejected folders.
---

# Human In The Loop Approval

Use this skill whenever an action is sensitive.

## Sensitive Action Examples

- Outbound email to unknown contacts
- Financial actions
- Bulk or irreversible actions
- High-impact external communications

## Approval File Schema

Create markdown files in AI_Employee_Vault/Pending_Approval with frontmatter:

- type: approval_request
- action: action identifier (example: send_email)
- created: ISO timestamp
- status: pending
- risk: low, medium, high

Include body sections:

- Action summary
- Parameters
- Why approval is required
- What happens on approve
- What happens on reject

## State Transitions

1. pending: file in AI_Employee_Vault/Pending_Approval
2. approved: human moves file to AI_Employee_Vault/Approved
3. rejected: human moves file to AI_Employee_Vault/Rejected
4. resolved: executed or closed, then moved to AI_Employee_Vault/Done

## Execution Gate

- Execute only if approval file exists in AI_Employee_Vault/Approved.
- If file is in Rejected, do not execute; log and close.

## Safety Rules

- Never self-approve.
- Never execute based on intent alone; require folder state proof.
