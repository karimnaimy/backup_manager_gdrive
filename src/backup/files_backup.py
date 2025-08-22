"""Files backup module."""

import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from .drive_manager import GoogleDriveManager


class FilesBackup:
    """Handles file and directory backups using JSON configuration."""
    
    def __init__(self, files_config_path: Path, backup_prefix: str, compression_level: int):
        self.files_config_path = files_config_path
        self.backup_prefix = backup_prefix
        self.compression_level = compression_level
        self.temp_dir = Path("/tmp/backup")
        self.temp_dir.mkdir(exist_ok=True)
    
    def _load_config(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load and parse JSON config file with defaults."""
        if not self.files_config_path.exists():
            print(f"Files config not found: {self.files_config_path}")
            print("No files will be backed up. Copy files_config.example.json to files_config.json to configure file backups.")
            return {"directories": [], "files": []}
        
        try:
            with open(self.files_config_path, 'r') as f:
                data = json.load(f)
            
            # Ensure required keys exist
            return {
                "directories": data.get("directories", []),
                "files": data.get("files", [])
            }
        except Exception as e:
            print(f"Error loading files config: {e}")
            return {"directories": [], "files": []}
    
    def _get_item_defaults(self, item: Dict[str, Any], source_path: Path) -> Dict[str, Any]:
        """Apply defaults to config item."""
        return {
            "source": source_path,
            "name": item.get("name", source_path.name),
            "max": item.get("max", 1),
            "exclude": item.get("exclude", []) if source_path.is_dir() else []
        }
    
    def create_backup(self, drive_manager: GoogleDriveManager) -> bool:
        """Create files backup and upload to Drive."""
        config = self._load_config()
        
        if not config["directories"] and not config["files"]:
            print("No file paths configured for backup")
            return True
        
        print("Backing up files...")
        uploaded_count = 0
        
        try:
            # Process directories
            for dir_item in config["directories"]:
                if self._backup_directory(dir_item, drive_manager):
                    uploaded_count += 1
            
            # Process files
            for file_item in config["files"]:
                if self._backup_file(file_item, drive_manager):
                    uploaded_count += 1
            
            print(f"Files backup completed: {uploaded_count} items uploaded")
            return True
            
        except Exception as e:
            print(f"Files backup error: {e}")
            return False
        finally:
            self._cleanup_temp_files()
    
    def _backup_directory(self, dir_item: Dict[str, Any], drive_manager: GoogleDriveManager) -> bool:
        """Backup a single directory."""
        source_path = Path(dir_item["source"])
        
        if not source_path.exists():
            print(f"Warning: Directory does not exist: {source_path}")
            return False
        
        if not source_path.is_dir():
            print(f"Warning: Path is not a directory: {source_path}")
            return False
        
        item = self._get_item_defaults(dir_item, source_path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.temp_dir / f"{self.backup_prefix}_files_{item['name']}_{timestamp}.tar.gz"
        
        try:
            # Create tarball
            self._create_tarball(source_path, backup_file, item["exclude"])
            
            # Upload to Drive
            drive_manager.upload_files_backup(backup_file)
            
            # Cleanup old backups for this specific item
            if item["max"] > 0:
                drive_manager.cleanup_files_backups_by_name(f"{self.backup_prefix}_files_{item['name']}", item["max"])
            
            backup_file.unlink()
            return True
            
        except Exception as e:
            print(f"Failed to backup directory {source_path}: {e}")
            return False
    
    def _backup_file(self, file_item: Dict[str, Any], drive_manager: GoogleDriveManager) -> bool:
        """Backup a single file."""
        source_path = Path(file_item["source"])
        
        if not source_path.exists():
            print(f"Warning: File does not exist: {source_path}")
            return False
        
        if not source_path.is_file():
            print(f"Warning: Path is not a file: {source_path}")
            return False
        
        item = self._get_item_defaults(file_item, source_path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.temp_dir / f"{self.backup_prefix}_files_{item['name']}_{timestamp}"
        
        try:
            # Copy file
            shutil.copy2(source_path, backup_file)
            
            # Upload to Drive
            drive_manager.upload_files_backup(backup_file)
            
            # Cleanup old backups for this specific item
            if item["max"] > 0:
                drive_manager.cleanup_files_backups_by_name(f"{self.backup_prefix}_files_{item['name']}", item["max"])
            
            backup_file.unlink()
            return True
            
        except Exception as e:
            print(f"Failed to backup file {source_path}: {e}")
            return False
    
    def _create_tarball(self, source_path: Path, backup_file: Path, exclude_patterns: List[str]) -> None:
        """Create compressed tarball of directory."""
        def tar_filter(tarinfo):
            for pattern in exclude_patterns:
                if tarinfo.name.endswith(pattern.replace("*", "")):
                    return None
            return tarinfo
        
        with tarfile.open(backup_file, 'w:gz', compresslevel=self.compression_level) as tar:
            tar.add(source_path, arcname=source_path.name, filter=tar_filter)
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        for file_path in self.temp_dir.glob(f"{self.backup_prefix}_files_*"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Failed to cleanup {file_path}: {e}")