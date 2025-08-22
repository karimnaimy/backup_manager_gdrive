#!/usr/bin/env python3
"""Main backup script entry point."""

import argparse
import sys

from src.backup.config import get_settings
from src.backup.service import BackupService


def main() -> None:
    """Main entry point for the backup script."""
    parser = argparse.ArgumentParser(description="Server backup tool")
    parser.add_argument("--mysql", action="store_true", help="Backup MySQL databases only")
    parser.add_argument("--files", action="store_true", help="Backup files only")
    
    args = parser.parse_args()
    
    # Determine what to backup
    backup_mysql = True
    backup_files = True
    
    if args.mysql and not args.files:
        backup_files = False
    elif args.files and not args.mysql:
        backup_mysql = False
    
    try:
        # Load settings
        settings = get_settings()
        
        # Create and run backup service
        backup_service = BackupService(settings)
        backup_service.run_backup(backup_mysql=backup_mysql, backup_files=backup_files)
        
        print("Backup process completed successfully!")
        
    except KeyboardInterrupt:
        print("\nBackup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()