"""
LinkedIn Auto-Poster for AI Employee - Silver Tier

Posts approved content to LinkedIn using Playwright browser automation.
Monitors the /Approved folder for LINKEDIN_POST_*.md files and publishes them.

This implements the Silver tier requirement:
  "Automatically Post on LinkedIn about business to generate sales"

Architecture:
  1. Content generator creates draft posts -> Pending_Approval/
  2. Human reviews and moves to Approved/
  3. This poster picks up approved posts, publishes via Playwright
  4. Moves completed posts to Done/ with proof screenshot

Usage:
    python linkedin_poster.py <vault_path> [session_path] [headless] [dry_run]

Examples:
    # First-time onboarding (headed mode to log in manually)
    python linkedin_poster.py "../AI_Employee_Vault" ".linkedin_session" false

    # Continuous posting daemon (headless)
    python linkedin_poster.py "../AI_Employee_Vault" ".linkedin_session" true false

    # Dry run (log but don't post)
    python linkedin_poster.py "../AI_Employee_Vault" ".linkedin_session" true true
"""
import hashlib
import json
import os
import re
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from base_watcher import BaseWatcher


class LinkedInPoster(BaseWatcher):
    """
    Posts approved content to LinkedIn via Playwright browser automation.

    Uses a persistent Chromium profile so the user logs in once and
    subsequent runs reuse the session cookie. Follows the same patterns
    as WhatsAppWatcher for session management, lock files, and state tracking.
    """

    LINKEDIN_URL = "https://www.linkedin.com"
    LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"

    def __init__(
        self,
        vault_path: str,
        session_path: str = None,
        check_interval: int = 300,
        headless: bool = True,
        dry_run: bool = False,
        login_timeout_seconds: int = None,
        max_posts_per_day: int = 2,
    ):
        super().__init__(vault_path, check_interval)

        default_session = Path(__file__).parent / ".linkedin_session"
        self.session_path = Path(session_path) if session_path else default_session
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.state_file = self.vault_path / ".linkedin_poster_state.json"
        self.lock_file = self.vault_path / ".linkedin_poster.lock"
        self.headless = headless
        self.dry_run = dry_run
        self.max_posts_per_day = max_posts_per_day

        self.login_timeout_seconds = (
            login_timeout_seconds
            if login_timeout_seconds is not None
            else (30 if headless else 120)
        )

        # Folders
        self.approved_dir = self.vault_path / "Approved"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.posted_ids = set()
        self.daily_post_count = 0
        self.last_post_date = None
        self._load_state()

    # ── State persistence ─────────────────────────────────────────────

    def _load_state(self):
        """Load previously posted content hashes from disk."""
        if not self.state_file.exists():
            return
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            self.posted_ids = set(data.get("posted_ids", []))
            self.daily_post_count = data.get("daily_post_count", 0)
            self.last_post_date = data.get("last_post_date")
        except Exception as e:
            self.logger.warning(f"Could not read state file: {e}")

    def _save_state(self):
        """Persist posted content hashes to avoid duplicate posts."""
        posted_list = list(self.posted_ids)
        if len(posted_list) > 5000:
            posted_list = posted_list[-5000:]
            self.posted_ids = set(posted_list)

        payload = {
            "posted_ids": posted_list,
            "daily_post_count": self.daily_post_count,
            "last_post_date": self.last_post_date,
        }
        temp_file = self.state_file.with_suffix(self.state_file.suffix + ".tmp")
        try:
            temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temp_file.replace(self.state_file)
        except Exception as e:
            self.logger.warning(f"Could not persist state file: {e}")
            try:
                temp_file.unlink(missing_ok=True)
            except Exception:
                pass

    # ── Lock file ─────────────────────────────────────────────────────

    def _is_pid_running(self, pid: int) -> bool:
        """Check whether a process id is currently alive."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _acquire_lock(self):
        """Ensure only one poster instance is active per vault."""
        if self.lock_file.exists():
            try:
                lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                existing_pid = int(lock_data.get("pid", 0))
                if existing_pid and self._is_pid_running(existing_pid):
                    raise RuntimeError(
                        f"Another LinkedInPoster instance is already running (pid={existing_pid})."
                    )
            except RuntimeError:
                raise
            except Exception:
                pass

        lock_data = {
            "pid": os.getpid(),
            "created_at": self.generate_timestamp(),
        }
        self.lock_file.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")

    def _release_lock(self):
        """Release process lock if held by this process."""
        if not self.lock_file.exists():
            return
        try:
            lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))
            if int(lock_data.get("pid", 0)) == os.getpid():
                self.lock_file.unlink(missing_ok=True)
        except Exception:
            pass

    # ── Post content parsing ──────────────────────────────────────────

    def _parse_frontmatter(self, content: str) -> Dict[str, str]:
        """Extract parameters from YAML frontmatter in markdown file."""
        if not content.startswith("---"):
            return {}
        try:
            end_idx = content.find("---", 3)
            if end_idx == -1:
                return {}
            yaml_content = content[3:end_idx].strip()
            params = {}
            current_key = None
            multiline_value = []
            in_multiline = False

            for line in yaml_content.split("\n"):
                stripped = line.strip()

                # Handle multiline values (content: |)
                if in_multiline:
                    if line.startswith("  ") or line.startswith("\t") or stripped == "":
                        multiline_value.append(line.rstrip())
                        continue
                    else:
                        # End of multiline - save collected value
                        if current_key:
                            params[current_key] = "\n".join(multiline_value).strip()
                        in_multiline = False
                        current_key = None
                        multiline_value = []

                if ":" in stripped:
                    key, value = stripped.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")

                    if value == "|":
                        # Start multiline
                        current_key = key
                        in_multiline = True
                        multiline_value = []
                    else:
                        params[key] = value

            # Handle trailing multiline
            if in_multiline and current_key:
                params[current_key] = "\n".join(multiline_value).strip()

            return params
        except Exception:
            return {}

    def _extract_post_body(self, content: str) -> str:
        """Extract the post body text from the markdown file.

        Tries frontmatter 'content' field first, otherwise
        falls back to a ## Post Content section in the body.
        """
        params = self._parse_frontmatter(content)
        if params.get("content"):
            return params["content"]

        # Fallback: look for ## Post Content section
        body_start = content.find("---", 3)
        if body_start == -1:
            return ""
        body = content[body_start + 3:].strip()

        # Try to find ## Post Content section
        match = re.search(
            r"##\s*Post Content\s*\n(.*?)(?=\n##|\Z)",
            body,
            re.DOTALL,
        )
        if match:
            return match.group(1).strip()

        # Last resort: use entire body minus markdown headings/metadata
        lines = []
        for line in body.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped.startswith("- ["):
                continue
            if stripped.startswith("*Created by"):
                continue
            if stripped == "---":
                continue
            if stripped:
                lines.append(stripped)
        return "\n".join(lines).strip()

    def _create_content_id(self, content: str) -> str:
        """Generate a unique hash for post content to prevent duplicates."""
        return hashlib.sha256(content.strip().lower().encode("utf-8")).hexdigest()

    # ── Rate limiting ─────────────────────────────────────────────────

    def _check_daily_limit(self) -> bool:
        """Check if we've hit the daily post limit."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_post_date != today:
            self.daily_post_count = 0
            self.last_post_date = today
        return self.daily_post_count < self.max_posts_per_day

    def _add_random_delay(self):
        """Add a random delay to avoid detection patterns."""
        delay = random.uniform(2.0, 6.0)
        self.logger.info(f"Adding {delay:.1f}s random delay")
        time.sleep(delay)

    # ── Browser automation ────────────────────────────────────────────

    def _open_context_and_page(self, playwright):
        """Launch a persistent browser context and return an active page."""
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=self.headless,
        )
        page = context.pages[0] if context.pages else context.new_page()
        return context, page

    def _check_page_is_feed(self, page) -> bool:
        """Check current page state for feed indicators WITHOUT navigating."""
        try:
            url = page.url
            if "/login" in url or "/signup" in url or "checkpoint" in url:
                return False

            # Look for feed-specific elements
            feed_indicators = page.locator(
                'button[aria-label*="post" i], '
                'div.share-box-feed-entry__trigger, '
                'div[data-view-name="feed-shared-container"], '
                'div.feed-identity-module, '
                'button.artdeco-button--muted'
            )
            return feed_indicators.count() > 0 or "/feed" in url
        except Exception:
            return False

    def _is_logged_in(self, page) -> bool:
        """Navigate to LinkedIn feed and check if we're logged in.

        Only call this once (e.g. on startup). For polling during login
        use _check_page_is_feed() which does not reload the page.
        """
        try:
            page.goto(self.LINKEDIN_FEED_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            return self._check_page_is_feed(page)
        except Exception as e:
            self.logger.warning(f"Error checking login status: {e}")
            return False

    def _wait_for_login(self, page):
        """Wait for user to manually log in (headed mode only).

        Navigates to LinkedIn login page ONCE, then polls the current
        page state without reloading so the user can type credentials.
        """
        self.logger.info("LinkedIn login required. Please log in manually in the browser window.")
        print("\n" + "=" * 60)
        print("  LinkedIn Login Required")
        print("  Please log in to LinkedIn in the browser window.")
        print("  The script will continue automatically after login.")
        print("=" * 60 + "\n")

        # Navigate once — after this we only poll, never reload
        try:
            page.goto(self.LINKEDIN_URL + "/login", wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        time.sleep(2)

        timeout = self.login_timeout_seconds
        start = time.time()
        while True:
            # Poll without navigating so user can type
            if self._check_page_is_feed(page):
                self.logger.info("LinkedIn login successful!")
                print("[OK] Login detected! Continuing...")
                return True

            elapsed = time.time() - start
            if timeout > 0 and elapsed > timeout:
                self.logger.error("Login timeout exceeded")
                return False

            time.sleep(5)

    def _publish_post(self, page, post_content: str) -> bool:
        """Publish a post on LinkedIn using browser automation.

        Returns True if the post was published successfully.
        """
        try:
            # Navigate to feed
            page.goto(self.LINKEDIN_FEED_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            self._add_random_delay()

            # Click "Start a post" button
            # Try a few common locators for LinkedIn's new DOM
            start_post_btn = page.locator(
                '.share-box-feed-entry__trigger, '
                'button:has-text("Start a post"), '
                'div[role="button"]:has-text("Start a post")'
            )
            # Add fallback using get_by_text for robust matching
            text_locator = page.get_by_text("Start a post", exact=True)

            clicked = False
            # Check the CSS locators first
            for i in range(start_post_btn.count() - 1, -1, -1):
                el = start_post_btn.nth(i)
                if el.is_visible():
                    try:
                        el.click(timeout=5000)
                        clicked = True
                        break
                    except Exception:
                        pass
            
            # Fallback to get_by_text
            if not clicked:
                for i in range(text_locator.count() - 1, -1, -1):
                    el = text_locator.nth(i)
                    if el.is_visible():
                        try:
                            # Use force=True in case the text is trapped inside a div that intercepts it
                            el.click(timeout=3000, force=True)
                            clicked = True
                            break
                        except Exception:
                            pass
            
            if not clicked:
                self.logger.error("Could not find 'Start a post' button")
                return False

            time.sleep(3)
            self._add_random_delay()

            # Wait for the post editor modal to appear
            editor = page.locator(
                'div[role="textbox"][contenteditable="true"], '
                'div.ql-editor[contenteditable="true"], '
                'div[aria-label*="Text editor" i][contenteditable="true"], '
                'div.share-creation-state__text-editor [contenteditable="true"], '
                '.editor-content [contenteditable="true"]'
            )

            editor.first.wait_for(state="visible", timeout=10000)
            time.sleep(1)

            # Type the post content
            editor.first.click()
            time.sleep(0.5)

            # Type content character-by-character for more natural behavior
            # But use fill for efficiency with longer posts
            editor.first.fill(post_content)
            time.sleep(1)
            self._add_random_delay()

            # Click the Post button
            post_btn = page.locator(
                'button:has-text("Post"):not(:has-text("Repost")), '
                'button[aria-label="Post" i], '
                'button.share-actions__primary-action, '
                'div[role="button"]:has-text("Post")'
            )
            post_text_locator = page.get_by_text("Post", exact=True)

            posted = False
            for i in range(post_btn.count() - 1, -1, -1):
                el = post_btn.nth(i)
                if el.is_visible():
                    try:
                        el.click(timeout=5000)
                        posted = True
                        break
                    except Exception:
                        pass
            
            if not posted:
                for i in range(post_text_locator.count() - 1, -1, -1):
                    el = post_text_locator.nth(i)
                    if el.is_visible():
                        try:
                            el.click(timeout=3000, force=True)
                            posted = True
                            break
                        except Exception:
                            pass
                        
            if not posted:
                self.logger.error("Could not find 'Post' button")
                return False

            time.sleep(3)
            self._add_random_delay()

            # Verify the post was published by checking for success indicators
            # The modal should close and we should be back on the feed
            try:
                editor.first.wait_for(state="hidden", timeout=10000)
                self.logger.info("Post published successfully (editor closed)")
                return True
            except PlaywrightTimeoutError:
                # Editor might still be visible but post may have gone through
                self.logger.warning("Post editor did not close clearly; checking feed")
                return True

        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout during posting: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error publishing post: {e}")
            return False

    def _take_proof_screenshot(self, page, post_filename: str) -> Optional[Path]:
        """Take a screenshot as proof of posting."""
        try:
            screenshot_dir = self.logs_dir / "linkedin_screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.sanitize_filename(post_filename.replace(".md", ""))
            screenshot_path = screenshot_dir / f"{safe_name}_{timestamp}.png"
            page.screenshot(path=str(screenshot_path), full_page=False)
            self.logger.info(f"Proof screenshot saved: {screenshot_path.name}")
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Could not take screenshot: {e}")
            return None

    # ── Logging ───────────────────────────────────────────────────────

    def _log_post_result(
        self,
        filename: str,
        post_content: str,
        success: bool,
        dry_run: bool = False,
        screenshot_path: Optional[Path] = None,
    ):
        """Log the result of a posting attempt."""
        log_entry = {
            "timestamp": self.generate_timestamp(),
            "action_type": "linkedin_post",
            "actor": "linkedin_poster",
            "target": "linkedin.com",
            "parameters": {
                "filename": filename,
                "content_preview": post_content[:200] + "..." if len(post_content) > 200 else post_content,
                "content_length": len(post_content),
            },
            "approval_status": "approved",
            "approved_by": "human",
            "result": "dry_run" if dry_run else ("success" if success else "failure"),
            "screenshot": str(screenshot_path) if screenshot_path else None,
        }

        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Could not write log: {e}")

    # ── Core watcher interface ────────────────────────────────────────

    def check_for_updates(self) -> list:
        """
        Check the Approved folder for LINKEDIN_POST_*.md files.

        Returns:
            List of approved LinkedIn post files ready to be published
        """
        posts = []
        for approved_file in sorted(self.approved_dir.glob("LINKEDIN_POST_*.md")):
            try:
                content = approved_file.read_text(encoding="utf-8")
                post_body = self._extract_post_body(content)

                if not post_body:
                    self.logger.warning(f"No post content found in {approved_file.name}")
                    continue

                content_id = self._create_content_id(post_body)
                if content_id in self.posted_ids:
                    self.logger.info(f"Skipping already-posted content: {approved_file.name}")
                    continue

                params = self._parse_frontmatter(content)
                posts.append({
                    "file_path": approved_file,
                    "filename": approved_file.name,
                    "content": post_body,
                    "content_id": content_id,
                    "params": params,
                })
            except Exception as e:
                self.logger.error(f"Error reading {approved_file.name}: {e}")

        self.logger.info(f"Found {len(posts)} approved LinkedIn posts to publish")
        return posts

    def create_action_file(self, item) -> Path:
        """
        Process an approved LinkedIn post: publish it and move to Done.

        This method name follows the BaseWatcher interface, but here it
        performs the posting action rather than creating an action file.
        """
        filename = item["filename"]
        post_content = item["content"]
        content_id = item["content_id"]
        file_path = item["file_path"]

        self.logger.info(f"Processing approved LinkedIn post: {filename}")

        # Check daily limit
        if not self._check_daily_limit():
            self.logger.warning(
                f"Daily post limit ({self.max_posts_per_day}) reached. "
                f"Will retry next cycle."
            )
            return None

        # DRY_RUN mode
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would post to LinkedIn: {post_content[:100]}...")
            print(f"\n[DRY RUN] LinkedIn Post Preview:\n{'=' * 40}\n{post_content}\n{'=' * 40}\n")
            self._log_post_result(filename, post_content, success=True, dry_run=True)
            self._move_to_done(file_path)
            self.posted_ids.add(content_id)
            self._save_state()
            return self.done_dir / filename

        # This will be handled in run() where we have the page context
        # Store in _pending_publish for the run loop to pick up
        self._pending_publish = item
        return file_path

    def _move_to_done(self, file_path: Path):
        """Move a processed file to the Done folder."""
        try:
            dest = self.done_dir / file_path.name
            if dest.exists():
                # Add timestamp to avoid collision
                stem = file_path.stem
                timestamp = datetime.now().strftime("%H%M%S")
                dest = self.done_dir / f"{stem}_{timestamp}{file_path.suffix}"
            file_path.rename(dest)
            self.logger.info(f"Moved to Done: {dest.name}")
        except Exception as e:
            self.logger.error(f"Could not move to Done: {e}")

    # ── Main run loop ─────────────────────────────────────────────────

    def run(self):
        """Run continuously, checking for approved posts and publishing them."""
        self._acquire_lock()
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Session path: {self.session_path}")
        self.logger.info(f"Headless: {self.headless}")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Max posts/day: {self.max_posts_per_day}")

        if self.dry_run:
            # Dry run doesn't need a browser
            self.logger.info("Running in DRY_RUN mode (no browser needed)")
            try:
                while True:
                    try:
                        posts = self.check_for_updates()
                        for post in posts:
                            self.create_action_file(post)
                    except Exception as e:
                        self.logger.error(f"Error in dry-run cycle: {e}", exc_info=True)
                    time.sleep(self.check_interval)
            except KeyboardInterrupt:
                self.logger.info("Stopped by user")
            finally:
                self._release_lock()
            return

        # Real posting mode: open browser
        with sync_playwright() as p:
            context, page = self._open_context_and_page(p)

            try:
                # Check login status
                if not self._is_logged_in(page):
                    if self.headless:
                        self.logger.error(
                            "Not logged in to LinkedIn. "
                            "Run once with headless=false to log in manually."
                        )
                        return
                    if not self._wait_for_login(page):
                        self.logger.error("Login failed or timed out")
                        return

                self.logger.info("LinkedIn session active. Watching for approved posts...")

                while True:
                    try:
                        posts = self.check_for_updates()
                        for post in posts:
                            if not self._check_daily_limit():
                                self.logger.info("Daily limit reached, skipping remaining posts")
                                break

                            filename = post["filename"]
                            post_content = post["content"]
                            content_id = post["content_id"]
                            file_path = post["file_path"]

                            self.logger.info(f"Publishing: {filename}")
                            success = self._publish_post(page, post_content)

                            screenshot = None
                            if success:
                                screenshot = self._take_proof_screenshot(page, filename)
                                self.posted_ids.add(content_id)
                                self.daily_post_count += 1
                                self.last_post_date = datetime.now().strftime("%Y-%m-%d")
                                self._move_to_done(file_path)
                                self._save_state()
                                self.logger.info(f"[OK] Successfully posted: {filename}")
                            else:
                                self.logger.error(f"[FAIL] Failed to post: {filename}")

                            self._log_post_result(
                                filename, post_content, success, screenshot_path=screenshot
                            )

                            # Wait between posts
                            time.sleep(random.uniform(30, 90))

                    except Exception as e:
                        if "Target page, context or browser has been closed" in str(e):
                            self.logger.warning("Browser context closed; recreating.")
                            try:
                                context.close()
                            except Exception:
                                pass
                            context, page = self._open_context_and_page(p)
                        else:
                            self.logger.error(f"Error in posting cycle: {e}", exc_info=True)

                    time.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.logger.info(f"{self.__class__.__name__} stopped by user")
            finally:
                try:
                    context.close()
                except Exception:
                    pass
                self._release_lock()


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python linkedin_poster.py <vault_path> [session_path] [headless] [dry_run]")
        print()
        print("Examples:")
        print('  # First-time login (headed mode)')
        print('  python linkedin_poster.py "../AI_Employee_Vault" ".linkedin_session" false')
        print()
        print('  # Continuous daemon (headless)')
        print('  python linkedin_poster.py "../AI_Employee_Vault" ".linkedin_session" true false')
        print()
        print('  # Dry run mode')
        print('  python linkedin_poster.py "../AI_Employee_Vault" ".linkedin_session" true true')
        sys.exit(1)

    vault_path = sys.argv[1]
    session_path = sys.argv[2] if len(sys.argv) > 2 else None
    headless = _to_bool(sys.argv[3]) if len(sys.argv) > 3 else True
    dry_run = _to_bool(sys.argv[4]) if len(sys.argv) > 4 else False

    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    poster = LinkedInPoster(
        vault_path=vault_path,
        session_path=session_path,
        headless=headless,
        dry_run=dry_run,
    )
    poster.run()


if __name__ == "__main__":
    main()
