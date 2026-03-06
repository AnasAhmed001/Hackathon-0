# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Personal AI Employee Hackathon 0 project, building an autonomous "Digital FTE" (Full-Time Equivalent) that operates 24/7 to manage personal and business affairs. The system follows a local-first, agent-driven, human-in-the-loop architecture with Claude Code as the reasoning engine.

## Architecture Components

### Core Architecture
- **Brain**: Claude Code as the reasoning engine
- **Memory/GUI**: Obsidian (local Markdown) as the dashboard
- **Senses (Watchers)**: Python scripts monitoring inputs (Gmail, WhatsApp, filesystems)
- **Hands (MCP)**: Model Context Protocol servers for external actions

### Key Patterns Implemented
- **Watcher Pattern**: Python scripts monitor inputs and create `.md` files in `/Needs_Action` folders
- **Ralph Wiggum Loop**: Stop hook pattern that keeps Claude iterating until tasks are complete
- **Human-in-the-Loop (HITL)**: Sensitive actions require approval via file movement
- **Claim-by-Move Rule**: Prevents duplicate work in multi-agent scenarios

## Codebase Structure

The repository implements the Bronze Tier foundation with:
- AI_Employee_Vault/: Obsidian vault with Dashboard.md, Company_Handbook.md
- /Inbox, /Needs_Action, /Done, /Pending_Approval, /Plans folders
- scripts/: Python Watcher implementations (base_watcher.py, filesystem_watcher.py)

## Common Development Tasks

### Running the Filesystem Watcher
```bash
cd scripts
py -m pip install -r requirements.txt
py filesystem_watcher.py "D:\My Work\Hackathon-0\AI_Employee_Vault"
```

### Starting Claude Code Session
```bash
cd "D:\My Work\Hackathon-0\AI_Employee_Vault"
claude
```

### Installing Dependencies
```bash
cd scripts
py -m pip install -r requirements.txt
```

### Processing Action Items
After Watchers create items in /Needs_Action, Claude Code can process them with:
```
Check the /Needs_Action folder and process any pending items. Create a plan for each item and move completed items to /Done.
```

## Key Files and Directories

- Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md: Complete architectural blueprint and hackathon guide
- AI_Employee_Vault/: The Obsidian vault structure
- scripts/base_watcher.py: Abstract base class for all Watcher implementations
- scripts/filesystem_watcher.py: File system monitoring implementation
- scripts/requirements.txt: Python dependencies (currently just watchdog)
- README.md: Bronze Tier implementation guide
- Claude.md: Context documentation for AI assistants

## Development Guidelines

- Follow the Watcher pattern for monitoring external inputs
- Implement Human-in-the-Loop safety for sensitive actions
- Use the Ralph Wiggum loop for autonomous task completion
- All AI functionality should be implemented as Agent Skills
- Keep sensitive credentials separate from the Obsidian vault
- Implement proper error handling and retry logic in Watchers