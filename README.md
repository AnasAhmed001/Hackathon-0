# Bronze Tier: AI Employee Foundation

This folder contains the complete Bronze Tier implementation of the Personal AI Employee hackathon.

## What is Bronze Tier?

Bronze Tier is the **minimum viable deliverable** for the Personal AI Employee hackathon. It provides:

- ✅ Obsidian vault with Dashboard.md and Company_Handbook.md
- ✅ One working Watcher script (File System monitoring)
- ✅ Claude Code integration ready (reading/writing to vault)
- ✅ Basic folder structure: /Inbox, /Needs_Action, /Done
- ✅ Foundation for Silver/Gold tier upgrades

**Estimated Setup Time:** 8-12 hours

## Folder Structure

```
bronze-tier/
├── AI_Employee_Vault/          # Your Obsidian vault
│   ├── Dashboard.md            # Main dashboard/status page
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Inbox/                  # Drop folder for files to process
│   ├── Needs_Action/           # Action items created by Watcher
│   ├── Done/                   # Completed items archive
│   ├── Pending_Approval/       # Items awaiting human approval
│   ├── Plans/                  # Multi-step task plans
│   ├── Briefings/              # CEO briefings (Gold tier+)
│   └── Accounting/             # Financial records (Gold tier+)
└── scripts/
    ├── base_watcher.py         # Base class for all Watchers
    ├── filesystem_watcher.py   # File System Watcher implementation
    └── requirements.txt        # Python dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
cd bronze-tier/scripts
py -m pip install -r requirements.txt
```

### 2. Start the Filesystem Watcher

```bash
py filesystem_watcher.py "D:\My Work\Hackathon-0\bronze-tier\AI_Employee_Vault"
```

The watcher will:
- Monitor the `/Inbox` folder for new files
- Create action files in `/Needs_Action` when files are dropped
- Log all activity to `watcher.log`

### 3. Drop a File to Test

Simply copy any file into the `AI_Employee_Vault/Inbox/` folder. The Watcher will automatically create a corresponding `.md` action file in `Needs_Action/`.

### 4. Process with Claude Code

Open Claude Code and point it at your vault:

```bash
cd "D:\My Work\Hackathon-0\bronze-tier\AI_Employee_Vault"
claude
```

Then prompt:
```
Check the /Needs_Action folder and process any pending items. Create a plan for each item and move completed items to /Done.
```

## How It Works

### The Watcher Pattern

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Drop      │───▶│  Filesystem  │───▶│  Needs_Action/  │
│   File      │    │   Watcher    │    │  (action file)  │
│  (Inbox/)   │    │  (running)   │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│    Done/    │◀───│  Claude Code │◀───│  Human Reviews  │
│ (completed) │    │  processes   │    │  & directs      │
└─────────────┘    └──────────────┘    └─────────────────┘
```

### Action File Format

When a file is dropped, the Watcher creates a Markdown file like:

```markdown
---
type: file_drop
original_name: document.pdf
size: 1.23 MB
received: 2026-03-03T17:58:27
status: pending
priority: normal
---

# File Drop for Processing

## File Details
- **Original Name**: document.pdf
- **Size**: 1.23 MB
- **Received**: 2026-03-03T17:58:27

## Content/Context
*Add context about what needs to be done with this file*

## Suggested Actions
- [ ] Review file contents
- [ ] Determine required action
- [ ] Process and move to /Done when complete
```

## Configuration

### Watcher Settings

Edit `filesystem_watcher.py` to customize:

```python
# Check interval (default: 5 seconds for filesystem)
check_interval: int = 5

# Drop folder (defaults to vault/Inbox)
drop_folder: str = None
```

### Company Handbook Rules

Edit `Company_Handbook.md` to define your rules:
- Payment thresholds
- Communication guidelines
- Escalation rules
- Working hours

## Upgrading to Silver Tier

To extend to Silver tier, add:

1. **Gmail Watcher** - Monitor Gmail for important emails
2. **WhatsApp Watcher** - Monitor WhatsApp for urgent messages
3. **MCP Server** - Enable sending emails/actions
4. **Approval Workflow** - Human-in-the-loop for sensitive actions
5. **Scheduled Tasks** - Cron/Task Scheduler integration

## Troubleshooting

### Watcher not detecting files

1. Check `watcher.log` for errors
2. Ensure the Inbox folder path is correct
3. Verify the watcher process is running

### Action files not being created

1. Check file permissions on the vault folder
2. Ensure Python has write access
3. Review the log for specific error messages

### Stopping the Watcher

Press `Ctrl+C` in the terminal where the watcher is running.

## Next Steps

After completing Bronze tier:

1. ✅ Test the watcher with various file types
2. ✅ Process files manually with Claude Code
3. ⏭️ Add Gmail Watcher (Silver tier)
4. ⏭️ Add MCP servers for external actions
5. ⏭️ Implement approval workflows

## Resources

- [Main Hackathon Documentation](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Watcher Architecture](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md#watcher-architecture)
- [Claude Code Documentation](https://claude.com/product/claude-code)
- [Obsidian Download](https://obsidian.md/download)

---

*Bronze Tier Implementation - Personal AI Employee Hackathon 0*
