
"""
File System Watcher for AI Employee - Bronze Tier

Monitors a drop folder for new files and creates action files in /Needs_Action.
This is the simplest Watcher to implement for the Bronze tier.

Usage:
    python filesystem_watcher.py <vault_path> [drop_folder_path]
    
Example:
    python filesystem_watcher.py "D:\My Work\Hackathon-0\bronze-tier\AI_Employee_Vault"
"""
import sys
import time
import hashlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from base_watcher import BaseWatcher


class FileDropHandler(FileSystemEventHandler):
    """Handles file system events for the drop folder."""
    
    def __init__(self, watcher):
        self.watcher = watcher
        self.logger = watcher.logger
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        source_path = Path(event.src_path)
        self.logger.info(f'New file detected: {source_path.name}')
        
        # Create action file for this drop
        try:
            action_file = self.watcher.create_action_file({
                'path': source_path,
                'name': source_path.name,
                'size': source_path.stat().st_size
            })
            self.logger.info(f'Action file created: {action_file.name}')
        except Exception as e:
            self.logger.error(f'Error creating action file: {e}')


class FilesystemWatcher(BaseWatcher):
    """
    Watches a folder for new files and creates action items.
    
    This is ideal for Bronze tier as it requires no API credentials.
    Simply drop files into the Inbox folder and the Watcher will
    create corresponding action files in Needs_Action.
    """
    
    def __init__(self, vault_path: str, drop_folder: str = None, check_interval: int = 5):
        """
        Initialize the Filesystem Watcher.
        
        Args:
            vault_path: Path to the Obsidian vault
            drop_folder: Path to folder to watch (defaults to vault/Inbox)
            check_interval: Check interval in seconds (default: 5 for filesystem)
        """
        super().__init__(vault_path, check_interval)
        
        # Use Inbox folder as drop folder by default
        self.drop_folder = Path(drop_folder) if drop_folder else self.inbox
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed files by hash to avoid duplicates
        self.processed_hashes = set()
    
    def check_for_updates(self) -> list:
        """
        This method is not used in the traditional sense for filesystem watching.
        The Observer pattern handles event-driven detection.
        
        Returns:
            Empty list (events are handled directly)
        """
        return []
    
    def create_action_file(self, item) -> Path:
        """
        Create a Markdown action file for a dropped file.
        
        Args:
            item: Dict with 'path', 'name', 'size' keys
            
        Returns:
            Path to created action file
        """
        file_path = item['path']
        file_name = item['name']
        file_size = item['size']
        
        # Generate unique ID from filename and timestamp
        timestamp = self.generate_timestamp().replace(':', '-')
        safe_name = self.sanitize_filename(file_name)
        action_filename = f"FILE_DROP_{safe_name}_{timestamp}.md"
        action_path = self.needs_action / action_filename
        
        # Calculate file hash for deduplication
        file_hash = self._calculate_hash(file_path)
        if file_hash in self.processed_hashes:
            self.logger.info(f'Skipping already processed file: {file_name}')
            return None
        self.processed_hashes.add(file_hash)
        
        # Create action file content
        content = f"""---
type: file_drop
original_name: {safe_name}
size: {file_size}
received: {self.generate_timestamp()}
status: pending
priority: normal
---

# File Drop for Processing

## File Details
- **Original Name**: {safe_name}
- **Size**: {self._format_size(file_size)}
- **Received**: {self.generate_timestamp()}

## Content/Context
*Add context about what needs to be done with this file*

## Suggested Actions
- [ ] Review file contents
- [ ] Determine required action
- [ ] Process and move to /Done when complete

## Notes
*Add any additional notes here*

---
*Created by FilesystemWatcher - Bronze Tier*
"""
        
        action_path.write_text(content, encoding='utf-8')
        return action_path
    
    def run(self):
        """
        Start the filesystem observer loop.
        """
        self.logger.info(f'Starting FilesystemWatcher')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Drop folder: {self.drop_folder}')
        
        # Set up the observer
        event_handler = FileDropHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.drop_folder), recursive=False)
        observer.start()
        
        self.logger.info(f'Watching for new files in: {self.drop_folder}')
        self.logger.info('Press Ctrl+C to stop')
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            self.logger.info('FilesystemWatcher stopped by user')
        except Exception as e:
            observer.stop()
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise
        
        observer.join()
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for deduplication."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f'Error calculating hash: {e}')
            return str(file_path)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python filesystem_watcher.py <vault_path> [drop_folder]")
        print("\nExample:")
        print('  python filesystem_watcher.py "D:\\My Work\\Hackathon-0\\bronze-tier\\AI_Employee_Vault"')
        sys.exit(1)
    
    vault_path = sys.argv[1]
    drop_folder = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Validate vault path
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    watcher = FilesystemWatcher(vault_path, drop_folder)
    watcher.run()


if __name__ == '__main__':
    main()
