---
name: ai-vault-plan-generation
description: |
  Plan creation skill for complex multi-step tasks.
  Produces structured markdown plans in AI_Employee_Vault/Plans
  with explicit steps, dependencies, and completion checks.
---

# Plan Generation

Use this skill for complex tasks that cannot be safely completed in one step.

## When To Use

- Multiple dependent actions are required
- The task spans multiple folders or systems
- You need a traceable execution checklist

## Plan File Location

- AI_Employee_Vault/Plans

## Plan Structure

Use markdown plan files with frontmatter:

- created
- status: pending, in_progress, blocked, done
- priority
- source_item

Include sections:

- Objective
- Constraints
- Steps checklist
- Dependencies
- Risks and mitigations
- Completion criteria

## Interaction Rules

- Link each plan to a source file from Needs_Action.
- Update checkboxes during execution.
- If approval is needed mid-plan, create approval request and pause.

## Completion Rules

- Mark plan done only when all checklist items are complete.
- Move final plan file to AI_Employee_Vault/Done when closed.
