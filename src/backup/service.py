"""Backup service implementation."""

from .config import BackupSettings
from .drive_manager import GoogleDriveManager
from .mysql_backup import MySQLBackup
from .files_backup import FilesBackup


class BackupService:
    """Main backup service orchestrator."""
    
    def __init__(self, settings: BackupSettings):
        self.settings = settings
        self.drive_manager = GoogleDriveManager(settings.google_drive)
        
        self.mysql_backup = MySQLBackup(
            host=settings.mysql_host,
            user=settings.mysql_user,
            password=settings.mysql_password,
            databases=settings.mysql_databases,
            backup_prefix=settings.backup_name_prefix,
            max_backups=settings.max_database_backups,
            compression_level=settings.compression_level
        )
        
        self.files_backup = FilesBackup(
            files_config_path=settings.files_config_path,
            backup_prefix=settings.backup_name_prefix,
            compression_level=settings.compression_level
        )
    
    def run_backup(self, backup_mysql: bool = True, backup_files: bool = True) -> None:
        """Run backup process with selective backup options."""
        print("Starting backup process...")
        
        try:
            # Authenticate with Google Drive
            self.drive_manager.authenticate()
            
            success_count = 0
            
            # MySQL backup
            if backup_mysql:
                if self.mysql_backup.create_backup(self.drive_manager):
                    success_count += 1
                else:
                    print("MySQL backup failed")
            
            # Files backup  
            if backup_files:
                if self.files_backup.create_backup(self.drive_manager):
                    success_count += 1
                else:
                    print("Files backup failed")
            
            if success_count > 0:
                print(f"Backup completed successfully! ({success_count} backup types completed)")
            else:
                print("All backups failed")
                
        except Exception as e:
            print(f"Backup process failed: {e}")
            raise