#!/usr/bin/env python3
"""Configuration example and override script."""

from pathlib import Path
from src.backup.config import BackupSettings, BackupPath, GoogleDriveConfig

def create_custom_config():
    """Create a custom configuration programmatically."""
    
    # Custom backup paths
    backup_paths = [
        BackupPath(
            source=Path("/var/lib/mysql"),
            exclude=["*.log", "*.tmp"],
            compress=True
        ),
        BackupPath(
            source=Path("/var/www/uploads"),
            exclude=["cache/*", "temp/*"],
            compress=True
        ),
        BackupPath(
            source=Path("/etc/nginx"),
            compress=True
        ),
        BackupPath(
            source=Path("/home/user/important-configs"),
            compress=True
        )
    ]
    
    # Custom Google Drive config
    gdrive_config = GoogleDriveConfig(
        credentials_file=Path("./credentials.json"),
        token_file=Path("./token.json"),
        folder_id=None,  # Will upload to root, or set your folder ID here
        chunk_size=2*1024*1024  # 2MB chunks
    )
    
    # Create settings with overrides
    settings = BackupSettings(
        paths=backup_paths,
        backup_name_prefix="myserver",
        max_backups=5,
        compression_level=9,  # Maximum compression
        google_drive=gdrive_config,
        
        # Database settings
        mysql_databases=["wordpress", "nextcloud"],
        postgres_databases=["app_production"]
    )
    
    return settings

if __name__ == "__main__":
    # Example of how to use custom config
    from src.backup.service import BackupService
    
    settings = create_custom_config()
    backup_service = BackupService(settings)
    
    print("Configuration created successfully!")
    print(f"Backup paths: {[str(p.source) for p in settings.paths]}")
    print(f"MySQL databases: {settings.mysql_databases}")
    print(f"PostgreSQL databases: {settings.postgres_databases}")
    
    # Uncomment to run backup with custom config
    # backup_service.run_backup()