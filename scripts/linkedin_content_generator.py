"""
LinkedIn Content Generator for AI Employee - Silver Tier

Creates draft LINKEDIN_POST_*.md files in Pending_Approval/ for human review.
These files contain post content, hashtags, and metadata that the linkedin_poster.py
will publish after the human approves them.

This is the content-creation half of the Silver tier requirement:
  "Automatically Post on LinkedIn about business to generate sales"

Usage:
    python linkedin_content_generator.py <vault_path> <post_content> [hashtags]

Examples:
    python linkedin_content_generator.py "../AI_Employee_Vault" "Excited about our latest AI project!"
    python linkedin_content_generator.py "../AI_Employee_Vault" "Check out our new service" "AI,Automation,Business"
"""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Optional


class LinkedInContentGenerator:
    """
    Generates draft LinkedIn post files for the approval workflow.

    Creates LINKEDIN_POST_*.md files with proper frontmatter in
    Pending_Approval/ so the human can review before publishing.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.pending_dir = self.vault_path / "Pending_Approval"
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def create_post_draft(
        self,
        content: str,
        hashtags: Optional[List[str]] = None,
        visibility: str = "public",
        post_type: str = "business_update",
        source: str = "manual",
    ) -> Path:
        """
        Create a draft LinkedIn post file in Pending_Approval/.

        Args:
            content: The post text content
            hashtags: List of hashtags (without #)
            visibility: Post visibility (public, connections)
            post_type: Type of post (business_update, thought_leadership, etc.)
            source: How the post was created (manual, scheduled, claude)

        Returns:
            Path to the created draft file
        """
        if hashtags is None:
            hashtags = []

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_type = post_type.replace(" ", "_")[:30]
        filename = f"LINKEDIN_POST_{safe_type}_{timestamp}.md"
        file_path = self.pending_dir / filename

        # Build the full post text with hashtags
        hashtag_line = " ".join(f"#{tag.strip('#')}" for tag in hashtags) if hashtags else ""

        draft_content = f"""---
type: approval_request
action: post_linkedin
platform: linkedin
created: {datetime.now().isoformat()}
status: pending
risk: low
visibility: {visibility}
post_type: {post_type}
source: {source}
hashtags: [{', '.join(hashtags)}]
content: |
  {content}
  {f'{chr(10)}  {hashtag_line}' if hashtag_line else ''}
---

## Post Content

{content}
{f'{chr(10)}{hashtag_line}' if hashtag_line else ''}

## Post Details
- **Platform**: LinkedIn
- **Visibility**: {visibility}
- **Type**: {post_type}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Suggested Actions
- [ ] Review post content for accuracy and tone
- [ ] Verify hashtags are relevant
- [ ] Move to /Approved to publish
- [ ] Move to /Rejected to discard

## To Approve
Move this file to the `Approved/` folder.

## To Reject
Move this file to the `Rejected/` folder.

---
*Created by LinkedInContentGenerator - Silver Tier*
"""

        file_path.write_text(draft_content, encoding="utf-8")
        print(f"[OK] Draft post created: {file_path.name}")
        print(f"  Review in Obsidian: Pending_Approval/{filename}")
        print(f"  Move to Approved/ to publish, or Rejected/ to discard.")
        return file_path

    def create_business_update_post(
        self,
        update_text: str,
        hashtags: Optional[List[str]] = None,
    ) -> Path:
        """Create a business update post draft."""
        if hashtags is None:
            hashtags = ["Business", "Growth", "Innovation"]
        return self.create_post_draft(
            content=update_text,
            hashtags=hashtags,
            post_type="business_update",
        )

    def create_thought_leadership_post(
        self,
        insight: str,
        hashtags: Optional[List[str]] = None,
    ) -> Path:
        """Create a thought leadership post draft."""
        if hashtags is None:
            hashtags = ["Leadership", "Innovation", "AI"]
        return self.create_post_draft(
            content=insight,
            hashtags=hashtags,
            post_type="thought_leadership",
        )

    def create_milestone_post(
        self,
        milestone: str,
        hashtags: Optional[List[str]] = None,
    ) -> Path:
        """Create a milestone/achievement post draft."""
        if hashtags is None:
            hashtags = ["Milestone", "Achievement", "Growth"]
        return self.create_post_draft(
            content=milestone,
            hashtags=hashtags,
            post_type="milestone",
        )

    def read_business_context(self) -> dict:
        """
        Read business context from vault files to help Claude generate
        relevant post content.

        Returns:
            Dictionary with business context data
        """
        context = {}

        # Read Company Handbook
        handbook_path = self.vault_path / "Company_Handbook.md"
        if handbook_path.exists():
            context["handbook"] = handbook_path.read_text(encoding="utf-8")

        # Read Business Goals if they exist
        goals_path = self.vault_path / "Business_Goals.md"
        if goals_path.exists():
            context["goals"] = goals_path.read_text(encoding="utf-8")

        # Read Dashboard for current status
        dashboard_path = self.vault_path / "Dashboard.md"
        if dashboard_path.exists():
            context["dashboard"] = dashboard_path.read_text(encoding="utf-8")

        # Check for recent completed tasks
        done_dir = self.vault_path / "Done"
        if done_dir.exists():
            recent_done = sorted(done_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
            context["recent_completions"] = [f.name for f in recent_done]

        return context


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python linkedin_content_generator.py <vault_path> <post_content> [hashtags]")
        print()
        print("Arguments:")
        print("  vault_path     Path to the Obsidian vault")
        print("  post_content   The text content for the LinkedIn post")
        print("  hashtags       Comma-separated hashtags (optional)")
        print()
        print("Examples:")
        print('  python linkedin_content_generator.py "../AI_Employee_Vault" "Excited about AI!" "AI,Tech"')
        sys.exit(1)

    vault_path = sys.argv[1]
    post_content = sys.argv[2]
    hashtags = sys.argv[3].split(",") if len(sys.argv) > 3 else None

    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    generator = LinkedInContentGenerator(vault_path)
    generator.create_post_draft(content=post_content, hashtags=hashtags)


if __name__ == "__main__":
    main()
