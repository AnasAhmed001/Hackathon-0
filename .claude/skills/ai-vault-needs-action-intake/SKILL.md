---
name: ai-vault-needs-action-intake
description: |
  Intake and triage skill for files in AI_Employee_Vault/Needs_Action.
  Use when watcher-created action files need to be parsed, prioritized,
  and prepared for execution or planning.
---

# Needs Action Intake

Use this skill to process watcher outputs in AI_Employee_Vault/Needs_Action.

## When To Use

- New files appear in AI_Employee_Vault/Needs_Action
- You need to classify urgency and intent from watcher-generated markdown
- You need a consistent first-pass triage before planning or approval

## Inputs

- One or more markdown files in AI_Employee_Vault/Needs_Action
- Company rules from AI_Employee_Vault/Company_Handbook.md
- Operational context from AI_Employee_Vault/Dashboard.md

## Procedure

1. List files in AI_Employee_Vault/Needs_Action.
2. Open each file and parse YAML frontmatter first.
3. Extract at minimum:
   - type
   - from
   - subject
   - priority
   - status
4. Categorize item into one of:
   - info_only
   - response_needed
   - sensitive_action
   - complex_multistep
5. Set proposed next step:
   - direct processing for low-risk items
   - plan creation for complex items
   - approval workflow for sensitive items

## Output Contract

For each processed item, produce:

- Summary of intent
- Risk level: low, medium, high
- Required mode: direct, plan, approval
- Next destination folder decision:
  - keep in Needs_Action while processing
  - create plan in Plans
  - create approval request in Pending_Approval

## Safety Rules

- Do not send emails, payments, or irreversible actions directly from triage.
- Never delete source action files.
- Keep decisions traceable in markdown notes when possible.
