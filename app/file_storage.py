"""
File and media storage for Pablos bot.
Stores files/images uploaded by users with metadata.
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FileMetadata:
    """Metadata for a stored file."""
    
    def __init__(self, file_id: str, file_type: str, file_name: str, 
                 file_size: int, uploaded_at: str, description: Optional[str] = None):
        """
        Initialize file metadata.
        
        Args:
            file_id: Telegram file ID
            file_type: Type of file (photo, document, video, audio, voice)
            file_name: Original file name
            file_size: File size in bytes
            uploaded_at: Upload timestamp
            description: Optional description/caption
        """
        self.file_id = file_id
        self.file_type = file_type
        self.file_name = file_name
        self.file_size = file_size
        self.uploaded_at = uploaded_at
        self.description = description
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'file_id': self.file_id,
            'file_type': self.file_type,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileMetadata':
        """Create from dictionary."""
        return cls(
            file_id=data['file_id'],
            file_type=data['file_type'],
            file_name=data['file_name'],
            file_size=data['file_size'],
            uploaded_at=data['uploaded_at'],
            description=data.get('description')
        )


class FileStorage:
    """Manages file storage for users."""
    
    def __init__(self, storage_dir: str = "user_files"):
        """
        Initialize file storage.
        
        Args:
            storage_dir: Directory to store file metadata
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        logger.info(f"File storage initialized at {self.storage_dir}")
    
    def _get_user_file(self, user_id: int) -> Path:
        """Get path to user's metadata file."""
        return self.storage_dir / f"user_{user_id}.json"
    
    def _load_user_files(self, user_id: int) -> List[FileMetadata]:
        """Load user's file metadata."""
        user_file = self._get_user_file(user_id)
        if not user_file.exists():
            return []
        
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [FileMetadata.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error loading files for user {user_id}: {e}")
            return []
    
    def _save_user_files(self, user_id: int, files: List[FileMetadata]) -> None:
        """Save user's file metadata."""
        user_file = self._get_user_file(user_id)
        try:
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump([f.to_dict() for f in files], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving files for user {user_id}: {e}")
    
    def add_file(self, user_id: int, file_id: str, file_type: str, 
                 file_name: str, file_size: int, description: Optional[str] = None) -> None:
        """
        Add a file to user's storage.
        
        Args:
            user_id: User ID
            file_id: Telegram file ID
            file_type: Type of file
            file_name: File name
            file_size: File size in bytes
            description: Optional description
        """
        files = self._load_user_files(user_id)
        
        metadata = FileMetadata(
            file_id=file_id,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            uploaded_at=datetime.now().isoformat(),
            description=description
        )
        
        files.append(metadata)
        self._save_user_files(user_id, files)
        logger.info(f"Added {file_type} for user {user_id}: {file_name}")
    
    def get_user_files(self, user_id: int, file_type: Optional[str] = None) -> List[FileMetadata]:
        """
        Get user's files, optionally filtered by type.
        
        Args:
            user_id: User ID
            file_type: Optional file type filter
            
        Returns:
            List of file metadata
        """
        files = self._load_user_files(user_id)
        
        if file_type:
            files = [f for f in files if f.file_type == file_type]
        
        return files
    
    def get_file_count(self, user_id: int) -> int:
        """
        Get total number of files for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of files
        """
        return len(self._load_user_files(user_id))
    
    def clear_user_files(self, user_id: int) -> None:
        """
        Clear all files for a user.
        
        Args:
            user_id: User ID
        """
        user_file = self._get_user_file(user_id)
        if user_file.exists():
            user_file.unlink()
            logger.info(f"Cleared all files for user {user_id}")
    
    def get_recent_files(self, user_id: int, limit: int = 10) -> List[FileMetadata]:
        """
        Get user's most recent files.
        
        Args:
            user_id: User ID
            limit: Maximum number of files to return
            
        Returns:
            List of recent file metadata
        """
        files = self._load_user_files(user_id)
        # Sort by upload time (most recent first)
        files.sort(key=lambda f: f.uploaded_at, reverse=True)
        return files[:limit]
    
    def format_file_list(self, files: List[FileMetadata]) -> str:
        """
        Format file list for display.
        
        Args:
            files: List of file metadata
            
        Returns:
            Formatted string
        """
        if not files:
            return "Lu belum upload file apapun jir"
        
        lines = [f"📁 File lu ({len(files)} total):"]
        lines.append("")
        
        for i, file in enumerate(files, 1):
            # Format file size
            size_kb = file.file_size / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb/1024:.1f} MB"
            
            # Format upload time
            try:
                upload_time = datetime.fromisoformat(file.uploaded_at)
                time_str = upload_time.strftime("%d/%m/%Y %H:%M")
            except:
                time_str = "Unknown"
            
            # File type emoji
            emoji_map = {
                'photo': '🖼️',
                'document': '📄',
                'video': '🎥',
                'audio': '🎵',
                'voice': '🎤'
            }
            emoji = emoji_map.get(file.file_type, '📎')
            
            lines.append(f"{i}. {emoji} {file.file_name}")
            lines.append(f"   Type: {file.file_type} | Size: {size_str} | {time_str}")
            
            if file.description:
                lines.append(f"   Caption: {file.description}")
            
            lines.append("")
        
        return "\n".join(lines)

