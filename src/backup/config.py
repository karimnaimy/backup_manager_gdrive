"""Configuration settings using Pydantic v2."""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleDriveConfig(BaseModel):
    """Google Drive specific configuration."""
    
    credentials_file: Path = Field(default=Path("credentials/gdrive.json"), description="OAuth2 credentials file")
    token_file: Path = Field(default=Path("credentials/token.json"), description="Stored auth token file")
    folder_id: Optional[str] = Field(default=None, description="Google Drive folder ID to upload to")
    folder_name: str = Field(default="Server Backups", description="Google Drive folder name to create/use")
    chunk_size: int = Field(default=1024*1024, description="Upload chunk size in bytes")


class BackupSettings(BaseSettings):
    """Main backup configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BACKUP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Files configuration
    files_config_path: Path = Field(default=Path("files_config.json"), description="Path to files configuration JSON")
    
    # Backup settings
    backup_name_prefix: str = Field(default="server-backup", description="Prefix for backup file names")
    compression_level: int = Field(default=6, description="Compression level (0-9)")
    
    # Separate backup policies
    max_database_backups: int = Field(default=50, description="Maximum number of database backups to keep")
    max_files_backups: int = Field(default=0, description="Maximum number of files backups to keep (0 = no limit)")
    
    # Google Drive settings
    google_drive: GoogleDriveConfig = Field(default_factory=GoogleDriveConfig)
    
    # Database settings
    mysql_host: str = Field(default="localhost")
    mysql_user: str = Field(default="backup_user")
    mysql_password: str = Field(default="")
    mysql_databases: str = Field(default="", description="Comma-separated databases to backup")
    
    def get_mysql_databases(self) -> List[str]:
        """Get MySQL databases as a list."""
        if not self.mysql_databases.strip():
            return []
        return [db.strip() for db in self.mysql_databases.split(",")]
    


def get_settings() -> BackupSettings:
    """Get application settings."""
    return BackupSettings()