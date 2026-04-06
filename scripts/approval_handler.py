"""
Approval Handler for AI Employee - Silver Tier

Monitors the /Pending_Approval folder and processes approval files.
This implements the Silver tier requirement for human-in-the-loop approval workflow.
"""
import sys
import time
from pathlib import Path
import json
from datetime import datetime

from base_watcher import BaseWatcher


class ApprovalHandler(BaseWatcher):
    """
    Monitors the /Pending_Approval folder for approval files and processes them.

    When files are moved to /Approved/, triggers corresponding actions.
    When files are moved to /Rejected/, cancels corresponding actions.
    This implements the Silver tier requirement for human-in-the-loop approval workflow.
    """

    def __init__(self, vault_path: str, check_interval: int = 10):
        """
        Initialize the Approval Handler.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Check interval in seconds (default: 10 for quick response)
        """
        super().__init__(vault_path, check_interval)

        # Additional folders for approval workflow
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'

        # Create directories if they don't exist
        self.pending_approval.mkdir(parents=True, exist_ok=True)
        self.approved.mkdir(parents=True, exist_ok=True)
        self.rejected.mkdir(parents=True, exist_ok=True)

        # Track processed files to avoid duplicates
        self.processed_files = set()

        # Load previously processed files
        self._load_processed_files()

    def _load_processed_files(self):
        """Load previously processed files from a tracking file."""
        tracking_file = self.vault_path / '.approval_tracking.json'
        if tracking_file.exists():
            try:
                with open(tracking_file, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
            except Exception as e:
                self.logger.warning(f'Could not load tracking file: {e}')

    def _save_processed_files(self):
        """Save processed files to a tracking file."""
        tracking_file = self.vault_path / '.approval_tracking.json'
        try:
            with open(tracking_file, 'w') as f:
                json.dump({'processed_files': list(self.processed_files)}, f)
        except Exception as e:
            self.logger.error(f'Could not save tracking file: {e}')

    def check_for_updates(self):
        """
        Check for moved approval files in Approved and Rejected folders.

        Returns:
            List of approval action objects that need to be processed
        """
        actions = []

        # Check Approved folder
        for approved_file in self.approved.glob('*.md'):
            if approved_file.name not in self.processed_files:
                action = {
                    'type': 'approve',
                    'file_path': approved_file,
                    'original_name': approved_file.name
                }
                actions.append(action)
                self.processed_files.add(approved_file.name)

        # Check Rejected folder
        for rejected_file in self.rejected.glob('*.md'):
            if rejected_file.name not in self.processed_files:
                action = {
                    'type': 'reject',
                    'file_path': rejected_file,
                    'original_name': rejected_file.name
                }
                actions.append(action)
                self.processed_files.add(rejected_file.name)

        # Save tracking file
        self._save_processed_files()

        self.logger.info(f'Found {len(actions)} approval actions to process')
        return actions

    def create_action_file(self, action):
        """
        Process the approval action and trigger the corresponding external action.

        Args:
            action: Dictionary with action details

        Returns:
            Path to log file or None
        """
        try:
            action_type = action['type']
            file_path = action['file_path']
            original_name = action['original_name']

            # Read the approval file to get action details
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the YAML frontmatter to get action parameters
            yaml_params = self._parse_yaml_frontmatter(content)

            # Log the action
            log_entry = {
                'timestamp': self.generate_timestamp(),
                'action_type': action_type,
                'original_file': original_name,
                'parameters': yaml_params,
                'status': 'processed'
            }

            # Create log entry
            log_file = self.vault_path / 'Logs' / f"approval_{action_type}_{original_name.replace('.md', '')}_{int(datetime.now().timestamp())}.json"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(log_file, 'w') as f:
                json.dump(log_entry, f, indent=2)

            # Perform the action based on type
            if action_type == 'approve':
                self._perform_approved_action(yaml_params, file_path)
            elif action_type == 'reject':
                self._log_rejection(yaml_params, file_path)

            # Move the processed file to Done
            done_path = self.vault_path / 'Done' / file_path.name
            file_path.rename(done_path)

            self.logger.info(f'Processed {action_type} action for {original_name}')
            return log_file

        except Exception as e:
            self.logger.error(f'Error processing action {action.get("original_name", "unknown")}: {e}')
            return None

    def _parse_yaml_frontmatter(self, content):
        """Extract parameters from YAML frontmatter in markdown file."""
        if content.startswith('---'):
            try:
                end_idx = content.find('---', 3)  # Find closing ---
                if end_idx != -1:
                    yaml_content = content[4:end_idx].strip()
                    # Simple parsing of key: value pairs
                    params = {}
                    for line in yaml_content.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            params[key.strip()] = value.strip().strip('"\'')
                    return params
            except Exception:
                pass
        return {}

    def _perform_approved_action(self, params, original_file):
        """Perform the action that was approved."""
        action_type = params.get('action', 'unknown')
        self.logger.info(f'Performing approved action: {action_type}')

        # Based on the action type, perform the corresponding external action
        if action_type == 'send_email':
            self._send_approved_email(params)
        elif action_type == 'make_payment':
            self._make_approved_payment(params)
        elif action_type == 'post_social':
            self._post_approved_social(params)
        elif action_type == 'post_linkedin':
            self._post_approved_linkedin(params)
        else:
            self.logger.warning(f'Unknown action type: {action_type}')

    def _send_approved_email(self, params):
        """Send an email using MCP server based on approved parameters."""
        # This would typically call an MCP server to send the email
        recipient = params.get('to', 'Unknown')
        subject = params.get('subject', 'No Subject')
        self.logger.info(f'Sending approved email to {recipient}: {subject}')

        # In a real implementation, this would call the email MCP server
        # For now, we'll just log it
        print(f"[MCP CALL SIMULATION] Sending email to: {recipient}, subject: {subject}")

    def _make_approved_payment(self, params):
        """Make a payment based on approved parameters."""
        amount = params.get('amount', 'Unknown')
        recipient = params.get('recipient', 'Unknown')
        self.logger.info(f'Making approved payment of {amount} to {recipient}')

        # In a real implementation, this would call a payment MCP server
        # For now, we'll just log it
        print(f"[MCP CALL SIMULATION] Making payment: {amount} to {recipient}")

    def _post_approved_social(self, params):
        """Post to social media based on approved parameters."""
        platform = params.get('platform', 'Unknown')
        content = params.get('content', 'No content')
        self.logger.info(f'Posting approved content to {platform}')

        # In a real implementation, this would call a social media MCP server
        # For now, we'll just log it
        print(f"[MCP CALL SIMULATION] Posting to {platform}: {content[:50]}...")

    def _post_approved_linkedin(self, params):
        """Handle approved LinkedIn post.

        The linkedin_poster.py daemon picks up approved files directly
        from Approved/ folder. This handler logs the approval event
        so there's a record even if the poster processes it first.
        """
        content = params.get('content', 'No content')
        visibility = params.get('visibility', 'public')
        self.logger.info(
            f'LinkedIn post approved for publishing '
            f'(visibility={visibility}, length={len(content)} chars)'
        )
        print(f"[LINKEDIN] Approved for posting: {content[:80]}...")

    def _log_rejection(self, params, original_file):
        """Log that an action was rejected."""
        action_type = params.get('action', 'unknown')
        reason = params.get('reason', 'Not specified')
        self.logger.info(f'Rejected action: {action_type}, reason: {reason}')


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python approval_handler.py <vault_path>")
        print("\nExample:")
        print('  python approval_handler.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault"')
        sys.exit(1)

    vault_path = sys.argv[1]

    # Validate vault path
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    handler = ApprovalHandler(vault_path)
    handler.run()


if __name__ == '__main__':
    main()