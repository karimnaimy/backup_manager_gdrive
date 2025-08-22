"""MySQL backup module."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .drive_manager import GoogleDriveManager


class MySQLBackup:
    """Handles MySQL database backups."""
    
    def __init__(self, host: str, user: str, password: str, databases: str, 
                 backup_prefix: str, max_backups: int, compression_level: int):
        self.host = host
        self.user = user
        self.password = password
        self.databases = databases
        self.backup_prefix = backup_prefix
        self.max_backups = max_backups
        self.compression_level = compression_level
        self.temp_dir = Path("/tmp/backup")
        self.temp_dir.mkdir(exist_ok=True)
    
    def get_database_list(self) -> List[str]:
        """Get list of databases to backup."""
        if not self.databases.strip():
            return []
        return [db.strip() for db in self.databases.split(",")]
    
    def create_backup(self, drive_manager: GoogleDriveManager) -> bool:
        """Create MySQL backup and upload to Drive."""
        print("Backing up MySQL databases...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.temp_dir / f"{self.backup_prefix}_mysql_{timestamp}.sql"
        
        try:
            # Create mysqldump command
            cmd = [
                "mysqldump",
                f"--host={self.host}",
                f"--user={self.user}",
            ]
            
            if self.password:
                cmd.append(f"--password={self.password}")
            
            cmd.extend(["--single-transaction", "--routines", "--triggers"])
            
            databases = self.get_database_list()
            if databases:
                cmd.extend(databases)
            else:
                cmd.append("--all-databases")
            
            # Run mysqldump
            with open(backup_file, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            
            # Compress
            compressed_file = self._compress_file(backup_file)
            
            # Upload to Drive
            drive_manager.upload_database_backup(compressed_file)
            
            # Cleanup temp files
            compressed_file.unlink()
            
            # Cleanup old backups on Drive
            drive_manager.cleanup_database_backups(self.max_backups)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"MySQL backup failed: {e}")
            return False
        except Exception as e:
            print(f"MySQL backup error: {e}")
            return False
        finally:
            # Cleanup temp files
            for temp_file in [backup_file, backup_file.with_suffix('.sql.gz')]:
                if temp_file.exists():
                    temp_file.unlink()
    
    def _compress_file(self, file_path: Path) -> Path:
        """Compress SQL file."""
        import tarfile
        
        compressed_file = file_path.with_suffix('.sql.gz')
        
        with open(file_path, 'rb') as f_in:
            with tarfile.open(compressed_file, 'w:gz', compresslevel=self.compression_level) as tar:
                tarinfo = tarfile.TarInfo(name=file_path.name)
                tarinfo.size = file_path.stat().st_size
                tar.addfile(tarinfo, f_in)
        
        file_path.unlink()
        return compressed_file