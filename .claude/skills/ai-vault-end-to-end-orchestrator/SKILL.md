---
name: ai-vault-end-to-end-orchestrator
description: |
  Master coordination skill for the full AI employee loop:
  intake -> triage -> planning -> approval -> MCP action -> closure.
---

# End To End Orchestrator

Use this skill to run the complete Personal AI Employee workflow.

## Workflow State Machine

1. Intake
   - Read AI_Employee_Vault/Needs_Action
2. Triage
   - classify: direct, plan, approval
3. Plan
   - create/update AI_Employee_Vault/Plans when multi-step
4. Approval
   - create AI_Employee_Vault/Pending_Approval for sensitive actions
5. Execute
   - run approved actions only (for email: MCP send-email)
6. Close
   - move artifacts to AI_Employee_Vault/Done and log results

## Delegation Rules

- For intake details, use ai-vault-needs-action-intake.
- For routine execution, use ai-vault-action-processing.
- For sensitive actions, use ai-vault-approval-workflow.
- For multi-step tasks, use ai-vault-plan-generation.
- For outbound email execution, use ai-vault-email-mcp.
- For closure and logs, use ai-vault-task-closure-logging.

## Folder Contracts

- Inbox: external drops only
- Needs_Action: pending machine-readable tasks
- Pending_Approval: waiting for human decision
- Approved: executable approvals
- Rejected: blocked approvals
- Plans: active task roadmaps
- Done: completed artifacts
- Logs: audit trail

## Non-Negotiables

- Human approval gate for sensitive actions
- File state is the source of truth
- Full auditability from intake to closure
