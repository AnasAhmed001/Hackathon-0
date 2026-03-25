---
name: ai-vault-action-processing
description: |
  Action execution skill for routine, low-risk tasks derived from
  AI_Employee_Vault/Needs_Action files. Applies handbook rules and
  routes complex or sensitive tasks to plan or approval workflows.
---

# Action File Processing

Use this skill to process routine items after triage.

## When To Use

- A Needs_Action item is classified as low risk
- A response or update is needed without sensitive side effects

## Inputs

- AI_Employee_Vault/Needs_Action/*.md
- AI_Employee_Vault/Company_Handbook.md

## Procedure

1. Read the action file and suggested actions section.
2. Validate policy constraints from Company_Handbook.
3. If task is routine and safe, execute it.
4. If task becomes complex, hand off to plan generation.
5. If task becomes sensitive, hand off to approval workflow.

## Folder Interaction Rules

- Source: AI_Employee_Vault/Needs_Action
- Optional handoff outputs:
  - AI_Employee_Vault/Plans for multi-step work
  - AI_Employee_Vault/Pending_Approval for sensitive work
- Completion:
  - Move completed source item to AI_Employee_Vault/Done

## Safety Rules

- Never bypass approval for sensitive actions.
- Keep processing deterministic and auditable.
- Preserve original watcher metadata.
