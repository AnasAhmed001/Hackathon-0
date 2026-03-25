"""
Gmail Watcher for AI Employee - Silver Tier

Monitors Gmail for new important emails and creates action files in /Needs_Action.
This implements the Silver tier requirement for multiple watcher scripts.
"""
import sys
import time
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail account for new important emails and creates action items.

    This is part of the Silver tier requirement for multiple watcher scripts.
    """

    def __init__(self, vault_path: str, credentials_path: str, token_path: str = None, check_interval: int = 120):
        """
        Initialize the Gmail Watcher.

        Args:
            vault_path: Path to the Obsidian vault
            credentials_path: Path to the downloaded credentials.json file
            token_path: Path to token.json file (stores user's access and refresh tokens)
            check_interval: Check interval in seconds (default: 120 for Gmail to respect API limits)
        """
        super().__init__(vault_path, check_interval)

        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path) if token_path else self.vault_path / 'token.json'

        # Initialize Gmail service
        self.service = self._initialize_gmail_service()
        self.processed_ids = set()

    def _initialize_gmail_service(self):
        """Initialize the Gmail API service with proper authentication."""
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

        creds = None

        # Load existing token if available
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.warning(f'Token refresh failed: {e}')
                    # If refresh fails, we'll need to re-authenticate
                    creds = None

            if not creds:
                # Run the OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def check_for_updates(self):
        """
        Check Gmail for new important/unread emails.

        Returns:
            List of new email message objects that need action files created
        """
        try:
            # Query for unread important emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important after:2026-01-01'  # Adjust date as needed
            ).execute()

            messages = results.get('messages', [])
            new_messages = []

            for message in messages:
                if message['id'] not in self.processed_ids:
                    # Get the full message details
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()

                    new_messages.append(msg)
                    self.processed_ids.add(message['id'])

            self.logger.info(f'Found {len(new_messages)} new important emails')
            return new_messages

        except Exception as e:
            self.logger.error(f'Error checking for Gmail updates: {e}')
            return []

    def create_action_file(self, message) -> Path:
        """
        Create a Markdown action file for an email.

        Args:
            message: Gmail API message object

        Returns:
            Path to created action file
        """
        try:
            # Extract headers from the payload
            headers = {}
            if 'payload' in message and 'headers' in message['payload']:
                for header in message['payload']['headers']:
                    headers[header['name']] = header['value']

            # Extract snippet (preview text)
            snippet = message.get('snippet', '')

            # Generate unique filename
            email_id = message['id']
            timestamp = self.generate_timestamp().replace(':', '-')
            from_addr = headers.get('From', 'Unknown').split('<')[0].strip().replace('"', '')
            subject = headers.get('Subject', 'No Subject')
            safe_from = self.sanitize_filename(from_addr)[:50]  # Limit length
            safe_subject = self.sanitize_filename(subject)[:50]  # Limit length

            action_filename = f"GMAIL_{safe_from}_{safe_subject}_{timestamp}.md"
            action_path = self.needs_action / action_filename

            # Get label names
            label_ids = message.get('labelIds', [])
            label_names = []
            for label_id in label_ids:
                # Try to get readable label name (basic mapping, can be extended)
                label_map = {
                    'INBOX': 'Inbox',
                    'UNREAD': 'Unread',
                    'IMPORTANT': 'Important',
                    'SENT': 'Sent',
                    'DRAFT': 'Draft',
                    'TRASH': 'Trash',
                    'SPAM': 'Spam',
                    'CATEGORY_PERSONAL': 'Personal',
                    'CATEGORY_SOCIAL': 'Social',
                    'CATEGORY_PROMOTIONS': 'Promotions',
                    'CATEGORY_UPDATES': 'Updates',
                    'CATEGORY_FORUMS': 'Forums'
                }
                label_names.append(label_map.get(label_id, label_id))

            # Create action file content following the format from the document
            content = f"""---
type: email
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {headers.get('Date', self.generate_timestamp())}
priority: high
status: pending
gmail_id: {email_id}
labels: {', '.join(label_names)}
---

## Email Content
{snippet}

## Suggested Actions
- [ ] Review email content
- [ ] Determine required response
- [ ] Respond to sender if needed
- [ ] Process and move to /Done when complete

## Raw Headers
{chr(10).join([f"- **{h['name']}**: {h['value']}" for h in message['payload']['headers'][:10]]) if 'payload' in message and 'headers' in message['payload'] else ''}

---
*Created by GmailWatcher - Silver Tier*
"""

            action_path.write_text(content, encoding='utf-8')
            self.logger.info(f'Created Gmail action file: {action_path.name}')
            return action_path

        except Exception as e:
            self.logger.error(f'Error creating action file for email {message.get("id", "unknown")}: {e}')
            return None


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python gmail_watcher.py <vault_path> <credentials_path> [token_path]")
        print("\nExample:")
        print('  python gmail_watcher.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault" "D:\\path\\to\\credentials.json"')
        sys.exit(1)

    vault_path = sys.argv[1]
    credentials_path = sys.argv[2]
    token_path = sys.argv[3] if len(sys.argv) > 3 else None

    # Validate paths
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    if not Path(credentials_path).exists():
        print(f"Error: Credentials path does not exist: {credentials_path}")
        sys.exit(1)

    watcher = GmailWatcher(vault_path, credentials_path, token_path)
    watcher.run()


if __name__ == '__main__':
    main()