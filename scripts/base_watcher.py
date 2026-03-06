"""
Base Watcher Template for AI Employee
All Watcher scripts inherit from this base class.
"""
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class BaseWatcher(ABC):
    """
    Abstract base class for all Watcher scripts.
    
    Watchers monitor various inputs (Gmail, WhatsApp, filesystem, etc.)
    and create actionable .md files in the /Needs_Action folder.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the Watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.processed_ids = set()
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items to process.
        
        Returns:
            List of new items that need action files created
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created file
        """
        pass
    
    def run(self):
        """
        Main run loop. Continuously monitors for updates.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')
                except Exception as e:
                    self.logger.error(f'Error processing updates: {e}', exc_info=True)
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise
    
    def generate_timestamp(self) -> str:
        """Generate ISO format timestamp."""
        return datetime.now().isoformat()
    
    def sanitize_filename(self, name: str) -> str:
        """Remove invalid filename characters."""
        invalid_chars = '<>:"/\\|？*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
