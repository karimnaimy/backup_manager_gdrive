"""Google Drive operations manager."""

from pathlib import Path
from typing import Optional

from googleapiclient.http import MediaFileUpload

from .auth import GoogleDriveAuth
from .config import GoogleDriveConfig


class GoogleDriveManager:
    """Handles all Google Drive operations."""
    
    def __init__(self, config: GoogleDriveConfig):
        self.config = config
        self.auth = GoogleDriveAuth(config)
        self._main_folder_id = None
        self._database_folder_id = None
        self._files_folder_id = None
    
    def authenticate(self) -> None:
        """Authenticate with Google Drive."""
        self.auth.authenticate_headless()
        if not self.auth.test_connection():
            raise RuntimeError("Failed to connect to Google Drive")
        self._setup_folders()
    
    def _get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Get existing folder or create new one."""
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.auth.service.files().list(q=query, fields="files(id)").execute()
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            folder_metadata['parents'] = [parent_id]
        
        folder = self.auth.service.files().create(body=folder_metadata, fields='id').execute()
        print(f"Created folder: {folder_name}")
        return folder.get('id')
    
    def _setup_folders(self) -> None:
        """Setup main folder and database/files subfolders."""
        self._main_folder_id = self._get_or_create_folder(self.config.folder_name)
        self._database_folder_id = self._get_or_create_folder("database", self._main_folder_id)
        self._files_folder_id = self._get_or_create_folder("files", self._main_folder_id)
    
    def upload_database_backup(self, file_path: Path) -> str:
        """Upload database backup and return file ID."""
        return self._upload_file(file_path, self._database_folder_id)
    
    def upload_files_backup(self, file_path: Path) -> str:
        """Upload files backup and return file ID."""
        return self._upload_file(file_path, self._files_folder_id)
    
    def _upload_file(self, file_path: Path, folder_id: str) -> str:
        """Upload file to specified folder."""
        print(f"Uploading {file_path.name}...")
        
        file_metadata = {'name': file_path.name, 'parents': [folder_id]}
        media = MediaFileUpload(str(file_path), chunksize=self.config.chunk_size, resumable=True)
        
        request = self.auth.service.files().create(body=file_metadata, media_body=media, fields='id')
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Progress: {int(status.progress() * 100)}%")
        
        print(f"Uploaded: {file_path.name}")
        return response['id']
    
    def cleanup_database_backups(self, max_backups: int) -> None:
        """Cleanup old database backups."""
        self._cleanup_backups(self._database_folder_id, max_backups, "database")
    
    def cleanup_files_backups(self, max_backups: int) -> None:
        """Cleanup old files backups."""
        self._cleanup_backups(self._files_folder_id, max_backups, "files")
    
    def cleanup_files_backups_by_name(self, name_prefix: str, max_backups: int) -> None:
        """Cleanup old files backups by specific name prefix."""
        if max_backups <= 0:
            return
        
        query = f"name contains '{name_prefix}' and '{self._files_folder_id}' in parents and trashed=false"
        results = self.auth.service.files().list(
            q=query,
            orderBy='createdTime desc',
            fields="files(id,name)"
        ).execute()
        
        files = results.get('files', [])
        if len(files) > max_backups:
            for file in files[max_backups:]:
                self.auth.service.files().delete(fileId=file['id']).execute()
                print(f"Deleted: {file['name']}")
    
    def _cleanup_backups(self, folder_id: str, max_backups: int, backup_type: str) -> None:
        """Cleanup old backups in folder."""
        if max_backups <= 0:
            print(f"Cleanup disabled for {backup_type}")
            return
        
        query = f"'{folder_id}' in parents and trashed=false"
        results = self.auth.service.files().list(
            q=query,
            orderBy='createdTime desc',
            fields="files(id,name)"
        ).execute()
        
        files = results.get('files', [])
        if len(files) > max_backups:
            for file in files[max_backups:]:
                self.auth.service.files().delete(fileId=file['id']).execute()
                print(f"Deleted: {file['name']}")
        else:
            print(f"{backup_type}: {len(files)}/{max_backups} backups")