# AI Employee Skills

This directory contains modular skills for the Personal AI Employee workflow.

## Skill List

- ai-vault-needs-action-intake: Parse and triage watcher outputs in Needs_Action
- ai-vault-action-processing: Execute routine low-risk actions
- ai-vault-approval-workflow: Human-in-the-loop approval file lifecycle
- ai-vault-plan-generation: Build and manage Plans for complex tasks
- ai-vault-email-mcp: Execute approved email sends through MCP
- ai-vault-task-closure-logging: Move artifacts to Done and write logs
- ai-vault-watcher-operations: Start, monitor, and recover watcher processes
- ai-vault-end-to-end-orchestrator: Coordinate the full workflow

## Typical Sequence

1. Intake from Needs_Action
2. Route to direct processing, planning, or approval
3. Execute approved actions
4. Close tasks and archive to Done with logs
