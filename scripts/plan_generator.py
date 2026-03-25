"""
Plan Generator for AI Employee - Silver Tier

Creates structured Plan.md files for multi-step tasks.
This implements the Silver tier requirement for Claude reasoning loops that create Plan.md files.
"""
import sys
import time
from pathlib import Path
from datetime import datetime


class PlanGenerator:
    """
    Generates structured Plan.md files for multi-step tasks.

    This implements the Silver tier requirement for Claude reasoning loops
    that create Plan.md files to track multi-step tasks.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the Plan Generator.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.plans_dir = self.vault_path / 'Plans'
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def create_plan(self, task_description: str, steps: list = None, priority: str = "normal"):
        """
        Create a structured Plan.md file for a multi-step task.

        Args:
            task_description: Brief description of the task
            steps: List of steps to complete the task (optional)
            priority: Priority level (low, normal, high, critical)

        Returns:
            Path to the created plan file
        """
        # Generate unique plan filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_task = "".join(c for c in task_description[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_task = safe_task.replace(' ', '_')
        plan_filename = f"PLAN_{safe_task}_{timestamp}.md"
        plan_path = self.plans_dir / plan_filename

        # Default steps if none provided
        if steps is None:
            steps = [
                f"Review {task_description.lower()}",
                "Break down into subtasks",
                "Execute each subtask",
                "Verify completion",
                "Move to /Done when complete"
            ]

        # Create plan content
        plan_content = f"""---
task: "{task_description}"
created: {datetime.now().isoformat()}
status: pending
priority: {priority}
estimated_duration: TBD
depends_on: []
tags: ["silver-tier", "automated-plan"]
---

# Plan: {task_description}

**Status:** `[[pending]]` | **Priority:** `{priority}` | **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Objective
{task_description}

## Steps to Complete
{chr(10).join([f"- [ ] {step}" for step in steps])}

## Resources Needed
- [[AI_Employee_Vault]]

## Timeline
- **Started:**
- **Due:**
- **Completed:**

## Notes
*Add any additional notes about this plan here*

## Dependencies
- [ ] Prerequisite tasks if any

## Success Criteria
- [ ] All steps completed
- [ ] Task verified as complete
- [ ] Plan moved to /Done

---
*Created by PlanGenerator - Silver Tier*
"""

        # Write the plan file
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(plan_content)

        print(f"Created plan: {plan_path.name}")
        return plan_path

    def create_business_audit_plan(self):
        """
        Create a specialized plan for business auditing tasks.
        """
        task_desc = "Weekly Business Audit and CEO Briefing"
        steps = [
            "Collect revenue data from accounting systems",
            "Analyze task completion rates",
            "Identify bottlenecks in processes",
            "Generate summary report",
            "Schedule follow-up actions",
            "Archive completed tasks"
        ]

        return self.create_plan(task_desc, steps, priority="high")

    def create_email_response_plan(self, email_subject: str):
        """
        Create a plan for responding to an email.
        """
        task_desc = f"Respond to email: {email_subject}"
        steps = [
            f"Review email: {email_subject}",
            "Determine appropriate response",
            "Draft response considering company handbook guidelines",
            "Check for sensitive information requiring approval",
            "Send response or create approval request",
            "Log interaction in appropriate records"
        ]

        return self.create_plan(task_desc, steps)

    def create_social_media_plan(self, platform: str, content_type: str):
        """
        Create a plan for social media posting.
        """
        task_desc = f"Post {content_type} on {platform}"
        steps = [
            f"Prepare {content_type} content for {platform}",
            "Ensure content follows brand guidelines",
            "Schedule optimal posting time",
            "Publish post",
            "Monitor engagement",
            "Report metrics"
        ]

        return self.create_plan(task_desc, steps, priority="normal")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python plan_generator.py <vault_path> [task_description]")
        print("")
        print("Examples:")
        print('  python plan_generator.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault" "Respond to client inquiry"')
        print('  python plan_generator.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault" "Weekly business audit"')
        sys.exit(1)

    vault_path = sys.argv[1]
    task_description = sys.argv[2] if len(sys.argv) > 2 else "Generic task"

    # Validate vault path
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    generator = PlanGenerator(vault_path)

    # Create a generic plan
    generator.create_plan(task_description)


if __name__ == '__main__':
    main()