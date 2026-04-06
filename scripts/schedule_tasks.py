"""
Task Scheduler for AI Employee - Silver Tier

Handles basic scheduling of recurring tasks using Python's schedule library.
This implements the Silver tier requirement for basic scheduling via cron or Task Scheduler.
"""
import sys
import time
import schedule
from pathlib import Path
import subprocess
import threading
from datetime import datetime


class TaskScheduler:
    """
    Schedules recurring tasks for the AI Employee.

    This implements the Silver tier requirement for basic scheduling
    via cron or Task Scheduler. On Windows, this can work alongside
    Windows Task Scheduler. On Unix-like systems, it can work with cron.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the Task Scheduler.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / 'Logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def schedule_gmail_check(self, interval_minutes: int = 30):
        """
        Schedule Gmail checking at regular intervals.
        """
        def run_gmail_watcher():
            try:
                cmd = [
                    sys.executable,
                    str(Path(__file__).parent / "gmail_watcher.py"),
                    str(self.vault_path),
                    str(Path(__file__).parent / ".." / "credentials.json")
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                self._log_task_result("Gmail Check", result.returncode == 0, result.stdout, result.stderr)
            except Exception as e:
                self._log_task_result("Gmail Check", False, "", str(e))

        schedule.every(interval_minutes).minutes.do(run_gmail_watcher)
        print(f"Scheduled Gmail checking every {interval_minutes} minutes")

    def schedule_filesystem_check(self, interval_minutes: int = 5):
        """
        Schedule filesystem monitoring at regular intervals.
        """
        def run_filesystem_watcher():
            try:
                cmd = [
                    sys.executable,
                    str(Path(__file__).parent / "filesystem_watcher.py"),
                    str(self.vault_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                self._log_task_result("Filesystem Check", result.returncode == 0, result.stdout, result.stderr)
            except Exception as e:
                self._log_task_result("Filesystem Check", False, "", str(e))

        schedule.every(interval_minutes).minutes.do(run_filesystem_watcher)
        print(f"Scheduled filesystem checking every {interval_minutes} minutes")

    def schedule_daily_briefing(self, time_str: str = "08:00"):
        """
        Schedule daily briefing generation.
        """
        def run_daily_briefing():
            try:
                # This would typically call Claude Code to generate a briefing
                # For now, we'll just log it
                from plan_generator import PlanGenerator
                generator = PlanGenerator(self.vault_path)
                generator.create_plan(
                    f"Daily CEO Briefing {datetime.now().strftime('%Y-%m-%d')}",
                    [
                        "Collect yesterday's metrics",
                        "Analyze revenue trends",
                        "Identify operational bottlenecks",
                        "Generate executive summary",
                        "Prepare action items for today"
                    ],
                    priority="high"
                )
                self._log_task_result("Daily Briefing", True, "Briefing plan created", "")
            except Exception as e:
                self._log_task_result("Daily Briefing", False, "", str(e))

        schedule.every().day.at(time_str).do(run_daily_briefing)
        print(f"Scheduled daily briefing at {time_str}")

    def schedule_weekly_audit(self, day: str = "sunday", time_str: str = "06:00"):
        """
        Schedule weekly business audit.
        """
        def run_weekly_audit():
            try:
                # This would typically call Claude Code to generate an audit
                # For now, we'll just log it
                from plan_generator import PlanGenerator
                generator = PlanGenerator(self.vault_path)
                generator.create_business_audit_plan()
                self._log_task_result("Weekly Audit", True, "Audit plan created", "")
            except Exception as e:
                self._log_task_result("Weekly Audit", False, "", str(e))

        day_method = getattr(schedule.every(), day.lower())
        day_method.at(time_str).do(run_weekly_audit)
        print(f"Scheduled weekly audit every {day.capitalize()} at {time_str}")

    def schedule_linkedin_post(self, days: list = None, time_str: str = "10:00"):
        """
        Schedule LinkedIn content generation on specific days.

        Creates draft posts in Pending_Approval/ for human review.
        The linkedin_poster.py daemon handles publishing after approval.

        Args:
            days: Days of the week to post (default: Monday, Wednesday, Friday)
            time_str: Time to generate the post draft
        """
        if days is None:
            days = ["monday", "wednesday", "friday"]

        def run_linkedin_content_generation():
            try:
                from linkedin_content_generator import LinkedInContentGenerator
                generator = LinkedInContentGenerator(str(self.vault_path))

                # Create a placeholder post: Claude or the human will refine it
                day_name = datetime.now().strftime("%A")
                generator.create_post_draft(
                    content=(
                        f"[Draft — {day_name} LinkedIn post]\n\n"
                        f"Replace this text with your business update, insight, "
                        f"or achievement before approving."
                    ),
                    hashtags=["Business", "Innovation"],
                    post_type="business_update",
                    source="scheduled",
                )
                self._log_task_result(
                    "LinkedIn Post Draft", True,
                    "Draft created in Pending_Approval/", ""
                )
            except Exception as e:
                self._log_task_result("LinkedIn Post Draft", False, "", str(e))

        for day in days:
            day_method = getattr(schedule.every(), day.lower())
            day_method.at(time_str).do(run_linkedin_content_generation)

        print(f"Scheduled LinkedIn post generation on {', '.join(d.capitalize() for d in days)} at {time_str}")

    def _log_task_result(self, task_name: str, success: bool, stdout: str, stderr: str):
        """
        Log the result of a scheduled task.
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task': task_name,
            'success': success,
            'stdout': stdout[-500:] if len(stdout) > 500 else stdout,  # Limit log size
            'stderr': stderr[-500:] if len(stderr) > 500 else stderr,  # Limit log size
        }

        log_file = self.logs_dir / f"task_schedule_{datetime.now().strftime('%Y%m%d')}.json"
        with open(log_file, 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps(log_entry) + '\n')

    def run_scheduler(self):
        """
        Run the scheduler continuously.
        """
        print("Starting task scheduler...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")

    def list_scheduled_jobs(self):
        """
        List all scheduled jobs.
        """
        print("\nScheduled Jobs:")
        for job in schedule.jobs:
            print(f"  - {job}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python schedule_tasks.py <vault_path>")
        print("")
        print("Examples:")
        print('  python schedule_tasks.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault"')
        sys.exit(1)

    vault_path = sys.argv[1]

    # Validate vault path
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Create scheduler
    scheduler = TaskScheduler(vault_path)

    # Schedule default tasks
    scheduler.schedule_gmail_check(30)  # Every 30 minutes
    scheduler.schedule_filesystem_check(5)  # Every 5 minutes
    scheduler.schedule_daily_briefing("08:00")  # Every day at 8 AM
    scheduler.schedule_weekly_audit("sunday", "06:00")  # Every Sunday at 6 AM
    scheduler.schedule_linkedin_post(["monday", "wednesday", "friday"], "10:00")  # Mon/Wed/Fri at 10 AM

    # Show scheduled jobs
    scheduler.list_scheduled_jobs()

    # Run scheduler
    scheduler.run_scheduler()


if __name__ == '__main__':
    main()