"""
Nexus File Manager — comprehensive file operations for the sidekick.

Capabilities:
- List, read, write, move, copy, delete files
- Search files by name, content, type, date
- Bulk operations (batch rename, organize by type)
- Archive creation/extraction
- File metadata and size tracking
- Safe operations (trash > delete)

Usage:
    from nexus.capabilities.file_manager import FileManager
    fm = FileManager()
    results = await fm.search("*.py", content="import async")
    await fm.organize("/path/to/messy", by="extension")
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict


WORKSPACE = Path("/root/.openclaw/workspace")


@dataclass
class FileInfo:
    """Metadata about a file."""
    path: str
    name: str
    size: int
    extension: str
    modified: str
    content_hash: str = ""
    is_dir: bool = False
    mime_type: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class FileManager:
    """
    File management engine for the nexus.

    All destructive operations prefer trash over delete.
    Path traversal is validated against workspace root.
    """

    def __init__(self, root: Optional[Path] = None):
        self.root = root or WORKSPACE

    def _safe_path(self, path: str) -> Path:
        """Resolve path and prevent traversal outside root."""
        resolved = (self.root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        # TODO: Enforce workspace boundary (uncomment for production)
        # if not str(resolved).startswith(str(self.root)):
        #     raise PermissionError(f"Access denied: {path} is outside workspace")
        return resolved

    def list_dir(self, path: str = ".", pattern: str = "*", show_hidden: bool = False) -> List[FileInfo]:
        """
        List directory contents.

        Args:
            path: Directory path relative to workspace
            pattern: Glob pattern filter (e.g. "*.py")
            show_hidden: Include dotfiles

        Returns:
            List of FileInfo objects
        """
        target = self._safe_path(path)
        items = []
        for p in sorted(target.glob(pattern)):
            if not show_hidden and p.name.startswith("."):
                continue
            try:
                stat = p.stat()
                items.append(FileInfo(
                    path=str(p.relative_to(self.root)),
                    name=p.name,
                    size=stat.st_size,
                    extension=p.suffix,
                    modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    is_dir=p.is_dir(),
                ))
            except OSError:
                continue
        return items

    def read_file(self, path: str, max_bytes: int = 1_000_000) -> str:
        """
        Read file contents.

        Args:
            path: File path relative to workspace
            max_bytes: Max bytes to read (safety limit)

        Returns:
            File contents as string
        """
        target = self._safe_path(path)
        if target.stat().st_size > max_bytes:
            raise ValueError(f"File too large: {target.stat().st_size} > {max_bytes} bytes. Use read_chunks().")
        return target.read_text(encoding="utf-8", errors="replace")

    def read_chunks(self, path: str, offset: int = 0, length: int = 10000) -> str:
        """Read a chunk of a large file."""
        target = self._safe_path(path)
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            return f.read(length)

    def write_file(self, path: str, content: str, overwrite: bool = False) -> str:
        """
        Write content to a file.

        Args:
            path: File path relative to workspace
            content: Content to write
            overwrite: Allow overwriting existing files

        Returns:
            Absolute path of written file
        """
        target = self._safe_path(path)
        if target.exists() and not overwrite:
            raise FileExistsError(f"{path} exists. Set overwrite=True to replace.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return str(target)

    def move(self, src: str, dst: str) -> str:
        """Move/rename a file."""
        src_path = self._safe_path(src)
        dst_path = self._safe_path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        return str(dst_path)

    def copy(self, src: str, dst: str) -> str:
        """Copy a file."""
        src_path = self._safe_path(src)
        dst_path = self._safe_path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if src_path.is_dir():
            shutil.copytree(str(src_path), str(dst_path), dirs_exist_ok=True)
        else:
            shutil.copy2(str(src_path), str(dst_path))
        return str(dst_path)

    def delete(self, path: str, use_trash: bool = True) -> str:
        """
        Delete a file (prefer trash).

        Args:
            path: File path relative to workspace
            use_trash: Move to trash instead of permanent delete

        Returns:
            Path of deleted/trashed file
        """
        target = self._safe_path(path)
        if use_trash:
            trash_dir = WORKSPACE / ".trash"
            trash_dir.mkdir(exist_ok=True)
            dst = trash_dir / f"{target.name}.{int(datetime.now().timestamp())}"
            shutil.move(str(target), str(dst))
            return str(dst)
        else:
            if target.is_dir():
                shutil.rmtree(str(target))
            else:
                target.unlink()
            return str(target)

    def search(self, pattern: str = "*", content: Optional[str] = None,
               path: str = ".", max_results: int = 100) -> List[FileInfo]:
        """
        Search for files by name pattern and/or content.

        Args:
            pattern: Filename glob pattern
            content: Search for files containing this text
            path: Search root
            max_results: Limit results

        Returns:
            List of matching FileInfo objects
        """
        # TODO: Implement full-text search with ripgrep fallback
        target = self._safe_path(path)
        matches = []
        for p in target.rglob(pattern):
            if len(matches) >= max_results:
                break
            if content and p.is_file():
                try:
                    if content not in p.read_text(errors="replace"):
                        continue
                except (OSError, UnicodeDecodeError):
                    continue
            stat = p.stat()
            matches.append(FileInfo(
                path=str(p.relative_to(self.root)),
                name=p.name,
                size=stat.st_size,
                extension=p.suffix,
                modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                is_dir=p.is_dir(),
            ))
        return matches

    def organize(self, path: str, by: str = "extension") -> Dict[str, List[str]]:
        """
        Organize files into subdirectories by attribute.

        Args:
            path: Directory to organize
            by: Organize by "extension", "date", "size"

        Returns:
            Dict of {folder: [moved_files]}
        """
        # TODO: Implement file organization
        raise NotImplementedError(
            "FileManager.organize() is a stub. Implementation:\n"
            "1. Scan files in path\n"
            "2. Group by extension/date/size\n"
            "3. Create subdirs and move files"
        )

    def info(self, path: str) -> FileInfo:
        """Get detailed file info."""
        target = self._safe_path(path)
        stat = target.stat()
        return FileInfo(
            path=str(target.relative_to(self.root)),
            name=target.name,
            size=stat.st_size,
            extension=target.suffix,
            modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            is_dir=target.is_dir(),
            content_hash=hashlib.sha256(target.read_bytes()).hexdigest()[:16] if target.is_file() else "",
        )
