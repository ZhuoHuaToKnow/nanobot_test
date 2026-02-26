"""Nanobot data directory backup/restore functionality."""

import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable


def backup_nano_data(
    data_dir: Path,
    output_path: Path | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> Path:
    """
    Backup nanobot data directory (~/.nanobot) to a zip archive.

    The backup includes:
    - config.json (configuration)
    - workspace/ (agent workspace)
    - sessions/ (conversation sessions)
    - history/ (CLI history)
    - cron/ (scheduled jobs)
    - All other files in .nanobot directory

    Args:
        data_dir: Path to the nanobot data directory (~/.nanobot).
        output_path: Optional path for the output zip file. If None, generates
                     a filename with timestamp in current directory.
        on_progress: Optional callback for progress updates.

    Returns:
        Path to the created zip file.

    Raises:
        FileNotFoundError: If data_dir doesn't exist.
        OSError: If there's an error during zip creation.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Nanobot data directory not found: {data_dir}")

    # Generate output path if not provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = Path.cwd() / f"nanobot-backup-{timestamp}.zip"
    else:
        output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    progress("正在备份nanobot数据...")

    try:
        with zipfile.ZipFile(
            output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zipf:
            # Collect all files to archive
            files_to_add = []
            for item in data_dir.rglob("*"):
                if item.is_file():
                    # Calculate relative path from data dir root
                    # This preserves the directory structure in the archive
                    rel_path = item.relative_to(data_dir)
                    files_to_add.append((item, rel_path))

            # Add files to archive
            for file_path, rel_path in files_to_add:
                zipf.write(file_path, rel_path)

        # Calculate file size
        size_bytes = output_path.stat().st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        progress(f"备份完成: {output_path.name} ({size_str})")
        return output_path

    except Exception as e:
        # Clean up partial file if it exists
        if output_path.exists():
            output_path.unlink()
        raise OSError(f"Failed to create backup: {e}") from e


def restore_nano_data(
    archive_path: Path,
    data_dir: Path,
    merge: bool = False,
    backup: bool = True,
    on_progress: Callable[[str], None] | None = None,
) -> dict:
    """
    Restore nanobot data directory from a backup archive.

    Args:
        archive_path: Path to the backup zip archive.
        data_dir: Target nanobot data directory path (~/.nanobot).
        merge: If True, preserve existing files. If False, replace all.
        backup: If True, create backup of existing data before restore.
        on_progress: Optional callback for progress updates.

    Returns:
        Dictionary with restore statistics:
        {
            "files_imported": int,
            "files_skipped": int,
            "backup_path": Path | None
        }

    Raises:
        FileNotFoundError: If archive_path doesn't exist.
        ValueError: If archive is not a valid zip file.
        OSError: If there's an error during restore.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Backup not found: {archive_path}")

    if not zipfile.is_zipfile(archive_path):
        raise ValueError(f"Not a valid backup archive: {archive_path}")

    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    backup_path: Path | None = None

    try:
        # Create backup if data dir exists and backup is enabled
        if data_dir.exists() and backup:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = data_dir.parent / f"{data_dir.name}.backup.{timestamp}"
            progress(f"备份现有数据到 {backup_path.name}...")
            shutil.copytree(data_dir, backup_path)

        # Create data directory if it doesn't exist
        data_dir.mkdir(parents=True, exist_ok=True)

        progress("验证备份格式...")
        progress("正在恢复...")

        files_imported = 0
        files_skipped = 0

        with zipfile.ZipFile(archive_path, "r") as zipf:
            # Get list of files in archive
            file_list = zipf.namelist()

            # Extract files
            for member in file_list:
                # Skip directories in the file count (they're created implicitly)
                if member.endswith("/"):
                    target_path = data_dir / member
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path = data_dir / member

                # Handle merge mode
                if merge and target_path.exists():
                    files_skipped += 1
                    continue

                # Ensure parent directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Extract file
                with zipf.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())
                files_imported += 1

        progress(f"恢复完成: {files_imported} 个文件")
        if files_skipped > 0:
            progress(f"跳过: {files_skipped} 个已存在文件 (合并模式)")

        return {
            "files_imported": files_imported,
            "files_skipped": files_skipped,
            "backup_path": backup_path,
        }

    except Exception as e:
        # Rollback: restore from backup if available
        if backup_path and backup_path.exists():
            progress(f"恢复失败，正在从备份回滚...")
            if data_dir.exists():
                shutil.rmtree(data_dir)
            shutil.copytree(backup_path, data_dir)
            shutil.rmtree(backup_path)

        raise OSError(f"Failed to restore nanobot data: {e}") from e
