"""
WhatsApp Watcher for AI Employee - Silver Tier

Monitors WhatsApp Web for unread chats and creates action files in /Needs_Action.
This is an additional watcher to satisfy the Silver tier requirement for 2+ watchers.
"""
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import List, Dict, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for unread chat previews and creates action items.

    This watcher uses a persistent Playwright browser profile so the user can
    scan QR once and keep the session for future runs.
    """

    def __init__(
        self,
        vault_path: str,
        session_path: str = None,
        check_interval: int = 45,
        headless: bool = True,
        login_timeout_seconds: int = None,
        reprocess_existing: bool = False,
    ):
        super().__init__(vault_path, check_interval)

        default_session = Path(__file__).parent / ".whatsapp_session"
        self.session_path = Path(session_path) if session_path else default_session
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.state_file = self.vault_path / ".whatsapp_watcher_state.json"
        self.lock_file = self.vault_path / ".whatsapp_watcher.lock"
        self.headless = headless
        self.reprocess_existing = reprocess_existing
        self.max_processed_ids = 10000
        # Keep a longer timeout for first-time QR onboarding in headed mode.
        self.login_timeout_seconds = (
            login_timeout_seconds
            if login_timeout_seconds is not None
            else (30 if headless else 0)
        )

        self.keywords = {
            "urgent",
            "asap",
            "invoice",
            "payment",
            "help",
            "proposal",
            "quote",
            "meeting",
        }

        self.processed_ids = set()
        self._load_state()

    def _is_pid_running(self, pid: int) -> bool:
        """Check whether a process id is currently alive."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _acquire_lock(self):
        """Ensure only one watcher instance is active per vault."""
        if self.lock_file.exists():
            try:
                lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                existing_pid = int(lock_data.get("pid", 0))
                if existing_pid and self._is_pid_running(existing_pid):
                    raise RuntimeError(
                        f"Another WhatsAppWatcher instance is already running (pid={existing_pid})."
                    )
            except RuntimeError:
                raise
            except Exception:
                # Corrupt or stale lock; overwrite below.
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

    def _load_state(self):
        """Load already-processed identifiers from disk."""
        if not self.state_file.exists():
            return

        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            self.processed_ids = set(data.get("processed_ids", []))
        except Exception as e:
            self.logger.warning(f"Could not read state file: {e}")

    def _save_state(self):
        """Persist processed identifiers to avoid duplicate action files."""
        # Keep the state bounded so long-running watchers don't grow indefinitely.
        processed_list = list(self.processed_ids)
        if len(processed_list) > self.max_processed_ids:
            processed_list = processed_list[-self.max_processed_ids:]
            self.processed_ids = set(processed_list)

        payload = {"processed_ids": processed_list}
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

    def _create_message_id(self, contact: str, preview: str) -> str:
        raw = f"{contact}|{preview}".strip().lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _safe_contact_for_filename(self, contact: str) -> str:
        """Normalize contact text so generated filenames are portable."""
        normalized = unicodedata.normalize("NFKD", contact or "Unknown")
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = re.sub(r"\s+", " ", ascii_text).strip()
        return self.sanitize_filename(ascii_text)[:60] or "Unknown"

    def _open_context_and_page(self, playwright):
        """Launch or relaunch a persistent browser context and return an active page."""
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=self.headless,
        )
        page = context.pages[0] if context.pages else context.new_page()
        return context, page

    def _extract_unread_rows(self, page) -> List[Dict[str, Any]]:
        """
        Extract unread chat rows from WhatsApp Web.

        The selectors are intentionally broad to tolerate minor UI changes.
        """
        unread_badges = page.locator(
            'span[aria-label*="unread"], div[aria-label*="unread"], [data-testid*="unread"], span[data-icon*="unread"], div[data-icon*="unread"]'
        )
        unread_count = min(unread_badges.count(), 200)
        chat_list_count = page.locator('[data-testid="chat-list"]').count()
        cell_frame_count = page.locator('[data-testid="cell-frame-container"]').count()
        self.logger.info(
            f"WhatsApp selector snapshot: chat_list={chat_list_count}, "
            f"cell_frame_container={cell_frame_count}, unread_badges={unread_count}"
        )
        out: List[Dict[str, Any]] = []
        seen = set()

        for i in range(unread_count):
            badge = unread_badges.nth(i)
            try:
                ancestors = badge.evaluate(
                    """
                    (el) => {
                      const out = [];
                      let node = el;
                      for (let i = 0; i < 20 && node; i++) {
                        out.push((node.innerText || '').trim());
                        node = node.parentElement;
                      }
                      return out;
                    }
                    """
                )
            except Exception:
                continue

            if not isinstance(ancestors, list):
                continue

            text = ""
            banned = {"all", "unread", "groups"}
            for candidate in ancestors:
                if not candidate:
                    continue
                normalized = candidate.strip()
                if not normalized:
                    continue
                if normalized.lower() in banned:
                    continue

                lines = [x.strip() for x in normalized.splitlines() if x.strip()]
                if len(lines) < 2 or len(lines) > 6:
                    continue

                # Typical chat rows have compact text blocks.
                if 12 <= len(normalized) <= 260:
                    text = normalized
                    break

            if not text or text in seen:
                continue

            seen.add(text)
            lines = [x.strip() for x in text.splitlines() if x.strip()]
            if lines:
                first = lines[0].lower()
                if "unread message" in first:
                    continue
            out.append(
                {
                    "contact": lines[0] if lines else "Unknown",
                    "preview": lines[-1] if lines else "",
                    "raw": text,
                }
            )

        if out:
            self.logger.info(f"Unread rows matched from badges: {len(out)}")
            return out

        # Fallback: some UI variants do not expose unread badges in stable selectors.
        rows = page.locator(
            'div[role="listitem"], div[aria-rowindex], [data-testid="cell-frame-container"], '
            '[data-testid="cell-frame-title"], [data-testid="cell-frame-secondary"], div[role="button"]'
        )
        total = min(rows.count(), 30)
        self.logger.info(f"Fallback row candidates: {total}")
        out = []
        for i in range(total):
            row = rows.nth(i)
            try:
                text = (row.inner_text(timeout=800) or "").strip()
            except Exception:
                continue

            if not text:
                continue

            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if len(lines) < 2:
                continue

            out.append(
                {
                    "contact": lines[0],
                    "preview": lines[-1],
                    "raw": text,
                }
            )

        return out

    def _check_for_updates_on_page(self, page) -> List[Dict[str, Any]]:
        """Check a loaded WhatsApp page and build new actionable items."""
        items: List[Dict[str, Any]] = []

        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        selector_timeout = (
            self.login_timeout_seconds * 1000
            if self.login_timeout_seconds > 0
            else 0
        )
        page.wait_for_selector(
            'div[role="grid"], div[role="list"], [data-testid="chat-list"]',
            timeout=selector_timeout,
        )

        unread_rows = self._extract_unread_rows(page)
        matched_unread = len(unread_rows)
        skipped_processed = 0

        for row in unread_rows:
            contact = row.get("contact", "Unknown")
            preview = row.get("preview", "")
            msg_id = self._create_message_id(contact, preview)

            if (not self.reprocess_existing) and msg_id in self.processed_ids:
                skipped_processed += 1
                continue

            lower_preview = preview.lower()
            matched = [kw for kw in self.keywords if kw in lower_preview]
            priority = "high" if matched else "normal"

            items.append(
                {
                    "id": msg_id,
                    "contact": contact,
                    "preview": preview,
                    "raw": row.get("raw", ""),
                    "priority": priority,
                    "matched_keywords": matched,
                }
            )

        self.logger.info(
            f"Unread summary: matched={matched_unread}, "
            f"already_processed={skipped_processed}, new={len(items)}"
        )
        return items

    def check_for_updates(self):
        """
        Check WhatsApp Web for unread chats.

        Returns:
            List of unread chat previews that need action files
        """
        with sync_playwright() as p:
            context = None
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                )
                page = context.pages[0] if context.pages else context.new_page()
                return self._check_for_updates_on_page(page)
            except PlaywrightTimeoutError:
                self.logger.warning(
                    "WhatsApp Web chat list not ready before timeout. "
                    "Rerun in non-headless mode with larger login timeout to scan QR."
                )
                return []
            except Exception as e:
                self.logger.error(f"Error checking WhatsApp updates: {e}")
                return []
            finally:
                if context is not None:
                    try:
                        context.close()
                    except Exception:
                        pass

    def run(self):
        """Run continuously while keeping one persistent browser context."""
        self._acquire_lock()
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")

        with sync_playwright() as p:
            context, page = self._open_context_and_page(p)

            try:
                while True:
                    try:
                        items = self._check_for_updates_on_page(page)
                        for item in items:
                            self.create_action_file(item)
                    except PlaywrightTimeoutError:
                        self.logger.warning(
                            "WhatsApp Web chat list not ready before timeout. "
                            "If needed, run non-headless once to refresh session."
                        )
                    except Exception as e:
                        # Recover from browser/page shutdown without manual restart.
                        if "Target page, context or browser has been closed" in str(e):
                            self.logger.warning("Browser context closed; recreating context.")
                            try:
                                context.close()
                            except Exception:
                                pass
                            context, page = self._open_context_and_page(p)
                        else:
                            self.logger.error(f"Error processing updates: {e}", exc_info=True)

                    time.sleep(self.check_interval)
            except KeyboardInterrupt:
                self.logger.info(f"{self.__class__.__name__} stopped by user")
            finally:
                try:
                    context.close()
                except Exception:
                    pass
                self._release_lock()

    def create_action_file(self, item) -> Path:
        """
        Create a markdown action file for an unread WhatsApp chat preview.
        """
        msg_id = item["id"]
        contact = item.get("contact", "Unknown")
        preview = item.get("preview", "")
        raw_text = item.get("raw", "")
        priority = item.get("priority", "normal")
        matched = item.get("matched_keywords", [])

        timestamp = self.generate_timestamp().replace(":", "-")
        safe_contact = self._safe_contact_for_filename(contact)
        action_filename = f"WHATSAPP_{safe_contact}_{timestamp}.md"
        action_path = self.needs_action / action_filename

        content = f"""---
type: whatsapp
from: {contact}
received: {self.generate_timestamp()}
priority: {priority}
status: pending
whatsapp_id: {msg_id}
matched_keywords: {', '.join(matched)}
---

## Message Preview
{preview}

## Suggested Actions
- [ ] Open chat and review full context
- [ ] Decide if reply is required
- [ ] Draft response if needed
- [ ] Route sensitive actions to /Pending_Approval
- [ ] Move completed item to /Done

## Raw Extract
{raw_text}

---
*Created by WhatsAppWatcher - Silver Tier*
"""

        action_path.write_text(content, encoding="utf-8")
        self.processed_ids.add(msg_id)
        self._save_state()
        self.logger.info(f"Created WhatsApp action file: {action_path.name}")
        return action_path


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python whatsapp_watcher.py <vault_path> [session_path] [check_interval] [headless] [login_timeout_seconds] [onboarding_only] [reprocess_existing]")
        print("")
        print("Examples:")
        print('  python whatsapp_watcher.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault"')
        print('  python whatsapp_watcher.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault" "D:\\My Work\\Hackathon-0\\scripts\\.whatsapp_session" 45 false')
        print('  python whatsapp_watcher.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault" "D:\\My Work\\Hackathon-0\\scripts\\.whatsapp_session" 45 false 600')
        print('  python whatsapp_watcher.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault" "D:\\My Work\\Hackathon-0\\scripts\\.whatsapp_session" 45 false 0 true')
        print('  python whatsapp_watcher.py "D:\\My Work\\Hackathon-0\\AI_Employee_Vault" "D:\\My Work\\Hackathon-0\\scripts\\.whatsapp_session" 45 false 0 false true')
        sys.exit(1)

    vault_path = sys.argv[1]
    session_path = sys.argv[2] if len(sys.argv) > 2 else None

    check_interval = 45
    if len(sys.argv) > 3:
        try:
            check_interval = int(sys.argv[3])
        except ValueError:
            print(f"Invalid check_interval: {sys.argv[3]}")
            sys.exit(1)

    headless = True
    if len(sys.argv) > 4:
        headless = _to_bool(sys.argv[4])

    login_timeout_seconds = None
    if len(sys.argv) > 5:
        try:
            login_timeout_seconds = int(sys.argv[5])
        except ValueError:
            print(f"Invalid login_timeout_seconds: {sys.argv[5]}")
            sys.exit(1)

    onboarding_only = False
    if len(sys.argv) > 6:
        onboarding_only = _to_bool(sys.argv[6])

    reprocess_existing = False
    if len(sys.argv) > 7:
        reprocess_existing = _to_bool(sys.argv[7])

    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    watcher = WhatsAppWatcher(
        vault_path=vault_path,
        session_path=session_path,
        check_interval=check_interval,
        headless=headless,
        login_timeout_seconds=login_timeout_seconds,
        reprocess_existing=reprocess_existing,
    )

    # Optional one-time onboarding/session setup mode.
    if onboarding_only:
        watcher._acquire_lock()
        print("Starting WhatsApp onboarding mode (non-headless).")
        print("Scan QR once; after successful login, rerun with headless=true for continuous watching.")
        try:
            watcher.check_for_updates()
        finally:
            watcher._release_lock()
        print("Onboarding cycle finished. Now run in headless mode for background operation.")
        return

    watcher.run()


if __name__ == "__main__":
    main()
