import os
import zipfile
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile
from app.core.config import settings


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".c": "c",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".rs": "rust",
    ".scala": "scala",
    ".lua": "lua",
    ".sh": "bash",
    ".log": "log",
    ".txt": "text",
}


def get_file_language(filename: str) -> Optional[str]:
    ext = Path(filename).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext)


def is_supported_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


async def save_upload_file(upload_file: UploadFile, task_id: int) -> str:
    task_dir = os.path.join(settings.UPLOAD_DIR, str(task_id))
    os.makedirs(task_dir, exist_ok=True)

    unique_filename = f"{uuid.uuid4().hex}_{upload_file.filename}"
    file_path = os.path.join(task_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path


def extract_zip(zip_path: str, task_id: int) -> Tuple[str, List[str]]:
    extract_dir = os.path.join(settings.UPLOAD_DIR, str(task_id), "extracted")
    os.makedirs(extract_dir, exist_ok=True)

    extracted_files = []

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, extract_dir)
                extracted_files.append(relative_path)

    return extract_dir, extracted_files


def get_all_files(directory: str, extensions: Optional[List[str]] = None) -> List[Tuple[str, str]]:
    files = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in filenames:
            if filename.startswith('.'):
                continue

            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, directory)
            language = get_file_language(filename)

            if extensions is None or (language and language in extensions):
                files.append((relative_path, file_path))

    return files


def cleanup_task_files(task_id: int):
    task_dir = os.path.join(settings.UPLOAD_DIR, str(task_id))
    if os.path.exists(task_dir):
        shutil.rmtree(task_dir)


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


def read_file_lines(file_path: str, max_lines: int = 10000) -> List[str]:
    lines = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line)
    return lines
