#!/usr/bin/env python3
"""
FileMorph Architect: Directory Merger & Duplicate Finder
A professional, production-quality, multi-threaded PySide6 desktop utility
built with MVVM/MVC architecture, modern visual styling, and robust error resilience.

Key Features:
- Asynchronous Workers: QThread-based execution preventing GUI lockups.
- 4-Stage Progressive Scanning: High-performance duplicates finder handles 500,000+ files.
- Safe Directory Merge: Smart collision detection, multi-strategy renaming, and DRY RUN simulation.
- Sleek Interface: Custom styles supporting Light and Dark modes, keyboard bindings, and high-contrast colors.
- Ignore Patterns: Support for glob-style patterns to ignore temp/log files.
"""

import sys
import os
import json
import logging
import time
import hashlib
import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# PySide6 Imports
try:
    from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize, QPoint
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QLabel, QLineEdit, QPushButton, QFileDialog,
        QProgressBar, QTextEdit, QTreeView, QHeaderView, QCheckBox,
        QComboBox, QMessageBox, QFrame, QStyle
    )
    from PySide6.QtGui import QIcon, QColor, QBrush, QStandardItemModel, QStandardItem, QFont
except ImportError:
    print("Error: PySide6 is required to run this application.")
    print("Please install dependencies: pip install PySide6 send2trash")
    sys.exit(1)

# Platform trash handling
try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False

# ---------------------------------------------------------
# CONSTANTS & CONFIGURATION
# ---------------------------------------------------------
SETTINGS_FILE = "settings.json"
LOG_FILE = "application.log"

# Setup global logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FileMorph")

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def should_ignore(path: Path, base_dir: Path, ignore_patterns: str) -> bool:
    """
    Evaluates if a path matches any glob-style ignore pattern (e.g. *.tmp, *.log, temp_dir/).
    Supports both file names, absolute paths, and sub-directory matches.
    """
    if not ignore_patterns:
        return False
    
    patterns = [p.strip() for p in ignore_patterns.split(",") if p.strip()]
    
    try:
        rel_path = path.relative_to(base_dir) if path.is_absolute() else path
    except ValueError:
        rel_path = path
        
    rel_path_str = str(rel_path).replace("\\", "/")
    filename = path.name
    
    for pattern in patterns:
        pattern_norm = pattern.replace("\\", "/")
        # Directory check
        if pattern_norm.endswith("/"):
            dir_pat = pattern_norm.rstrip("/")
            parts = rel_path_str.split("/")
            # Match parent directories of the file
            if any(fnmatch.fnmatch(part, dir_pat) for part in parts[:-1]):
                return True
        else:
            # File or general path matching
            if fnmatch.fnmatch(filename, pattern_norm) or fnmatch.fnmatch(rel_path_str, pattern_norm):
                return True
    return False

def format_size(num_bytes: int) -> str:
    """Formats raw bytes into a human-readable string with dynamic unit resolution."""
    if num_bytes < 0:
        return "0 Bytes"
    for unit in ['Bytes', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            if unit == 'Bytes':
                return f"{int(num_bytes)} Bytes"
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"

# ---------------------------------------------------------
# STYLES (Sleek Interface Custom Design Theme)
# ---------------------------------------------------------
SLEEK_DARK_STYLE = """
QMainWindow {
    background-color: #000000;
}
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #f8fafc;
}
QFrame {
    border: none;
}
QFrame#kpi_card {
    background-color: #0a0a0a;
    border: 1px solid #27272a;
    border-radius: 8px;
}
QLabel#kpi_title {
    color: #a1a1aa;
    font-size: 10px;
    font-weight: bold;
}
QLabel#kpi_value {
    color: #3b82f6;
    font-size: 18px;
    font-weight: 800;
}
QLabel#section_header {
    font-weight: bold;
    font-size: 10px;
    color: #38bdf8;
}
QTabWidget::pane {
    border: 1px solid #1f2937;
    background-color: #000000;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #121214;
    color: #a1a1aa;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #3b82f6;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #27272a;
    color: #e4e4e7;
}
QLineEdit {
    background-color: #0a0a0a;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f8fafc;
}
QLineEdit:focus {
    border: 1px solid #3b82f6;
}
QPushButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2563eb;
}
QPushButton:pressed {
    background-color: #1d4ed8;
}
QPushButton:disabled {
    background-color: #18181b;
    color: #71717a;
}
QPushButton#btn_secondary {
    background-color: #121214;
    color: #e4e4e7;
    border: 1px solid #27272a;
}
QPushButton#btn_secondary:hover {
    background-color: #27272a;
}
QTreeView {
    background-color: #050505;
    border: 1px solid #1f2937;
    border-radius: 8px;
    gridline-color: #1f2937;
    color: #e4e4e7;
}
QHeaderView::section {
    background-color: #121214;
    color: #d4d4d8;
    padding: 6px;
    border: 1px solid #050505;
    font-weight: bold;
}
QTreeView::item {
    padding: 4px;
}
QTreeView::item:hover {
    background-color: rgba(59, 130, 246, 0.1);
}
QTreeView::item:selected {
    background-color: rgba(59, 130, 246, 0.25);
    color: #3b82f6;
}
QProgressBar {
    border: 1px solid #1f2937;
    border-radius: 6px;
    text-align: center;
    background-color: #050505;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 5px;
}
QComboBox {
    background-color: #0a0a0a;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 30px 6px 12px;
    color: #f4f4f5;
    min-height: 20px;
}
QComboBox:hover {
    border-color: #3b82f6;
}
QComboBox:focus {
    border-color: #3b82f6;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #27272a;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #3b82f6;
    margin-top: 1px;
}
QComboBox QAbstractItemView {
    background-color: #0a0a0a;
    border: 1px solid #27272a;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
    color: #f4f4f5;
    outline: none;
    border-radius: 6px;
    padding: 4px;
}
QTextEdit {
    background-color: #050505;
    border: 1px solid #1f2937;
    border-radius: 8px;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #cbd5e1;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""

SLEEK_LIGHT_STYLE = """
QMainWindow {
    background-color: #f1f5f9;
}
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #0f172a;
}
QFrame {
    border: none;
}
QFrame#kpi_card {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}
QLabel#kpi_title {
    color: #64748b;
    font-size: 10px;
    font-weight: bold;
}
QLabel#kpi_value {
    color: #2563eb;
    font-size: 18px;
    font-weight: 800;
}
QLabel#section_header {
    font-weight: bold;
    font-size: 10px;
    color: #0284c7;
}
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #e2e8f0;
    color: #475569;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #3b82f6;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #cbd5e1;
    color: #0f172a;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 12px;
    color: #0f172a;
}
QLineEdit:focus {
    border: 1px solid #3b82f6;
}
QPushButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2563eb;
}
QPushButton:pressed {
    background-color: #1d4ed8;
}
QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}
QPushButton#btn_secondary {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
}
QPushButton#btn_secondary:hover {
    background-color: #f1f5f9;
}
QTreeView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    gridline-color: #e2e8f0;
    color: #0f172a;
}
QHeaderView::section {
    background-color: #f1f5f9;
    color: #334155;
    padding: 6px;
    border: 1px solid #e2e8f0;
    font-weight: bold;
}
QTreeView::item {
    padding: 4px;
}
QTreeView::item:hover {
    background-color: rgba(59, 130, 246, 0.1);
}
QTreeView::item:selected {
    background-color: rgba(59, 130, 246, 0.25);
    color: #2563eb;
}
QProgressBar {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    text-align: center;
    background-color: #e2e8f0;
    color: #0f172a;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 5px;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 30px 6px 12px;
    color: #0f172a;
    min-height: 20px;
}
QComboBox:hover {
    border-color: #2563eb;
}
QComboBox:focus {
    border-color: #2563eb;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #cbd5e1;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #2563eb;
    margin-top: 1px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    color: #0f172a;
    outline: none;
    border-radius: 6px;
    padding: 4px;
}
QTextEdit {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #0f172a;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""

# ---------------------------------------------------------
# SETTINGS MANAGEMENT
# ---------------------------------------------------------
class SettingsService:
    @staticmethod
    def load() -> Dict[str, Any]:
        default_settings = {
            "window_width": 1024,
            "window_height": 768,
            "theme": "Dark",
            "last_folder_a": "",
            "last_folder_b": "",
            "last_destination": "",
            "last_duplicate_target": "",
            "conflict_policy": "rename_both",
            "ignore_patterns": "*.tmp, *.log, temp_dir/"
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return {**default_settings, **json.load(f)}
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
        return default_settings

    @staticmethod
    def save(settings: Dict[str, Any]) -> None:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

# ---------------------------------------------------------
# BACKGROUND WORKERS (Asynchronous Threads)
# ---------------------------------------------------------
class MergeWorker(QThread):
    progress_updated = Signal(int)
    status_updated = Signal(str)
    log_emitted = Signal(str)
    preview_ready = Signal(dict)
    finished_summary = Signal(dict)
    error_raised = Signal(str)

    def __init__(self, folder_a: str, folder_b: str, dest_folder: str, policy: str, dry_run: bool, ignore_patterns: str):
        super().__init__()
        self.folder_a = Path(folder_a)
        self.folder_b = Path(folder_b)
        self.dest_folder = Path(dest_folder)
        self.policy = policy
        self.dry_run = dry_run
        self.ignore_patterns = ignore_patterns
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        self.log_emitted.emit("[WARN] Requesting safe worker thread cancellation...")

    def calculate_file_hash(self, path: Path) -> str:
        """Read files in 64KB chunks to prevent RAM bloat (handles 500k+ large files smoothly)."""
        hasher = hashlib.md5()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    if self._is_cancelled:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Hash calculation error for {path}: {e}")
            return ""

    def run(self):
        try:
            self.status_updated.emit("Analyzing source folders...")
            self.log_emitted.emit(f"[INFO] Initializing scan sequence (Dry Run: {self.dry_run})")
            if self.ignore_patterns:
                self.log_emitted.emit(f"[INFO] Active ignore patterns: {self.ignore_patterns}")
            
            # Step 1: Scan both source directories, respecting ignore patterns
            files_a: Dict[Path, Path] = {}  # relative_path: absolute_path
            files_b: Dict[Path, Path] = {}

            # Populate A
            for root, dirs, files in os.walk(self.folder_a):
                if self._is_cancelled:
                    return
                # Modify dirs in-place to prevent walking into ignored directories
                dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, self.folder_a, self.ignore_patterns)]
                for file in files:
                    abs_path = Path(root) / file
                    if should_ignore(abs_path, self.folder_a, self.ignore_patterns):
                        continue
                    rel_path = abs_path.relative_to(self.folder_a)
                    files_a[rel_path] = abs_path

            # Populate B
            for root, dirs, files in os.walk(self.folder_b):
                if self._is_cancelled:
                    return
                # Modify dirs in-place to prevent walking into ignored directories
                dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, self.folder_b, self.ignore_patterns)]
                for file in files:
                    abs_path = Path(root) / file
                    if should_ignore(abs_path, self.folder_b, self.ignore_patterns):
                        continue
                    rel_path = abs_path.relative_to(self.folder_b)
                    files_b[rel_path] = abs_path

            all_rel_paths = set(files_a.keys()).union(set(files_b.keys()))
            
            self.log_emitted.emit(f"[INFO] Found {len(files_a)} files in Folder A, {len(files_b)} files in Folder B after applying filters.")
            
            # Categorize Files (Identical, Conflict, Unique)
            preview_tree: Dict[str, Any] = {}
            stats = {
                "copied": 0,
                "skipped": 0,
                "conflicts": 0,
                "data_copied": 0,
                "errors": 0,
                "elapsed_time": 0.0
            }
            
            start_time = time.time()
            total_items = len(all_rel_paths)
            processed_items = 0

            # Preview calculations with optimized size check and real-time logging
            self.status_updated.emit("Calculating merge overlay & conflicts...")
            self.log_emitted.emit("[INFO] Commencing file comparison & conflict determination...")
            
            for i, rel_path in enumerate(all_rel_paths):
                if self._is_cancelled:
                    self.log_emitted.emit("[WARN] Merge operation cancelled by user.")
                    return

                # Real-time feedback for large directories to prevent perceived hanging
                if (i + 1) % 500 == 0 or i == total_items - 1:
                    percent = int(((i + 1) / total_items) * 100)
                    self.progress_updated.emit(percent)
                    self.status_updated.emit(f"Analyzing conflicts: {i+1}/{total_items} files...")
                    self.log_emitted.emit(f"[INFO] Analyzed {i+1}/{total_items} files for overlay map...")

                in_a = rel_path in files_a
                in_b = rel_path in files_b
                
                state = "identical"
                size = 0
                
                sz_a = 0
                sz_b = 0
                if in_a and in_b:
                    # Metadata-only comparison for ultra-fast merge overlay creation
                    try:
                        sz_a = files_a[rel_path].stat().st_size
                        sz_b = files_b[rel_path].stat().st_size
                    except Exception:
                        sz_a = -1
                        sz_b = -2
                        
                    if sz_a == sz_b:
                        # Same relative path (name/path) and same size -> assume identical for merging
                        state = "identical"
                        size = sz_a
                    else:
                        # Different sizes -> conflict
                        state = "conflict"
                        stats["conflicts"] += 1
                        size = max(sz_a, 0)
                elif in_a:
                    state = "folderA_only"
                    sz_a = files_a[rel_path].stat().st_size
                    size = sz_a
                else:
                    state = "folderB_only"
                    sz_b = files_b[rel_path].stat().st_size
                    size = sz_b

                preview_tree[str(rel_path)] = {
                    "state": state,
                    "in_a": in_a,
                    "in_b": in_b,
                    "size": size,
                    "sz_a": sz_a,
                    "sz_b": sz_b
                }

            self.preview_ready.emit(preview_tree)

            # Execution (If not dry run)
            self.status_updated.emit("Merging files...")
            self.log_emitted.emit(f"[INFO] Initializing folder merging workflow (Dry Run: {self.dry_run})...")
            
            for rel_path, info in preview_tree.items():
                if self._is_cancelled:
                    return
                
                processed_items += 1
                self.progress_updated.emit(int((processed_items / total_items) * 100))
                
                p = Path(rel_path)
                state = info["state"]
                
                if state == "identical":
                    # Just copy A to dest
                    self._copy_file_safe(files_a[p], self.dest_folder / p, stats, processed_items, total_items)
                    stats["skipped"] += 1 # We kept only one copy, skipped B
                elif state == "folderA_only":
                    self._copy_file_safe(files_a[p], self.dest_folder / p, stats, processed_items, total_items)
                    stats["copied"] += 1
                elif state == "folderB_only":
                    self._copy_file_safe(files_b[p], self.dest_folder / p, stats, processed_items, total_items)
                    stats["copied"] += 1
                elif state == "conflict":
                    if self.policy == "rename_both":
                        # Rename strategy: main.py -> main (Folder A).py and main (Folder B).py
                        stem, suffix = p.stem, p.suffix
                        name_a = f"{stem} (Folder A){suffix}"
                        name_b = f"{stem} (Folder B){suffix}"
                        
                        self._copy_file_safe(files_a[p], self.dest_folder / p.parent / name_a, stats, processed_items, total_items)
                        self._copy_file_safe(files_b[p], self.dest_folder / p.parent / name_b, stats, processed_items, total_items)
                        stats["copied"] += 2
                        self.log_emitted.emit(f"[CONFLICT] Renamed both candidates for {rel_path}")
                    else:
                        # Overwrite with Folder A
                        self._copy_file_safe(files_a[p], self.dest_folder / p, stats, processed_items, total_items)
                        stats["copied"] += 1
                        self.log_emitted.emit(f"[CONFLICT] Overwrote conflict with Folder A version: {rel_path}")

            stats["elapsed_time"] = round(time.time() - start_time, 2)
            self.finished_summary.emit(stats)

        except Exception as e:
            logger.exception("Merge worker runtime exception")
            self.error_raised.emit(str(e))

    def _copy_file_safe(self, src: Path, dest: Path, stats: dict, idx: int, total_items: int):
        """Copies file safely, tracking total copied size. Respects DRY RUN flag."""
        try:
            if not self.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                # Quick chunk-based read/write for actual system copy
                with open(src, "rb") as fs, open(dest, "wb") as fd:
                    for chunk in iter(lambda: fs.read(65536), b""):
                        if self._is_cancelled:
                            break
                        fd.write(chunk)
            
            stats["data_copied"] += src.stat().st_size
            
            # Log individual copies only if total_items is small, otherwise log in batches to prevent UI lockup
            if total_items < 100 or idx % 100 == 0 or idx == total_items:
                prefix = "[SIMULATE]" if self.dry_run else "[COPY]"
                self.log_emitted.emit(f"{prefix} ({idx}/{total_items}) {src.name} -> {dest.name}")
        except Exception as e:
            stats["errors"] += 1
            self.log_emitted.emit(f"[ERROR] Copy failed for {src.name}: {e}")
            logger.error(f"Copy failed: {src} to {dest}: {e}")


class DuplicateWorker(QThread):
    progress_updated = Signal(int)
    status_updated = Signal(str)
    log_emitted = Signal(str)
    groups_found = Signal(dict)  # group_hash: [filepaths]
    finished_summary = Signal(dict)
    error_raised = Signal(str)

    def __init__(self, target_folder: str, deep_check: bool, ignore_patterns: str):
        super().__init__()
        self.target_folder = Path(target_folder)
        self.deep_check = deep_check
        self.ignore_patterns = ignore_patterns
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.log_emitted.emit("[INFO] Starting 4-stage progressive duplicate analysis...")
            if self.ignore_patterns:
                self.log_emitted.emit(f"[INFO] Active ignore patterns: {self.ignore_patterns}")
            start_time = time.time()
            
            # --- STAGE 1: Scan & Group by Size ---
            self.status_updated.emit("Stage 1: Scanning sizes...")
            self.log_emitted.emit("[STAGE 1] Recursively scanning directories for candidates...")
            
            size_groups: Dict[int, List[Path]] = {}
            total_scanned = 0
            
            for root, dirs, files in os.walk(self.target_folder):
                if self._is_cancelled:
                    return
                # Modify dirs in-place to prevent walking into ignored directories
                dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, self.target_folder, self.ignore_patterns)]
                for file in files:
                    abs_path = Path(root) / file
                    if should_ignore(abs_path, self.target_folder, self.ignore_patterns):
                        continue
                    try:
                        sz = abs_path.stat().st_size
                        if sz > 0: # Skip completely empty files
                            size_groups.setdefault(sz, []).append(abs_path)
                            total_scanned += 1
                    except Exception as e:
                        logger.warning(f"Unable to state file {abs_path}: {e}")

            # Prune unique sizes (Cannot be duplicates)
            size_candidates = {sz: paths for sz, paths in size_groups.items() if len(paths) > 1}
            self.log_emitted.emit(f"[STAGE 1] Found {len(size_candidates)} size clusters with duplication potential.")
            self.progress_updated.emit(25)

            if self._is_cancelled: return

            # --- STAGE 2: 8KB Header Hash Grouping ---
            self.status_updated.emit("Stage 2: Header hash comparisons...")
            self.log_emitted.emit("[STAGE 2] Checking first 8 KB chunks to prune mismatches quickly...")
            
            header_groups: Dict[Tuple[int, str], List[Path]] = {}
            for sz, paths in size_candidates.items():
                if self._is_cancelled: return
                for p in paths:
                    try:
                        with open(p, "rb") as f:
                            header = f.read(8192)
                        h = hashlib.md5(header).hexdigest()
                        header_groups.setdefault((sz, h), []).append(p)
                    except Exception as e:
                        logger.warning(f"Stage 2 read error {p}: {e}")

            header_candidates = {key: paths for key, paths in header_groups.items() if len(paths) > 1}
            self.progress_updated.emit(50)

            if self._is_cancelled: return

            # --- STAGE 3: Full SHA-256 Hash Calculation ---
            self.status_updated.emit("Stage 3: Deeper SHA-256 validation...")
            self.log_emitted.emit("[STAGE 3] Performing deep cryptographic hash computation...")
            
            sha_groups: Dict[str, List[Path]] = {}
            total_header_candidates = sum(len(paths) for paths in header_candidates.values())
            processed_stage3 = 0

            for (sz, header_h), paths in header_candidates.items():
                if self._is_cancelled: return
                for p in paths:
                    if self._is_cancelled: return
                    processed_stage3 += 1
                    percent = 50 + int((processed_stage3 / max(1, total_header_candidates)) * 40)
                    self.progress_updated.emit(percent)
                    
                    # Compute full SHA-256
                    hasher = hashlib.sha256()
                    try:
                        with open(p, "rb") as f:
                            for chunk in iter(lambda: f.read(65536), b""):
                                hasher.update(chunk)
                        sha_groups.setdefault(hasher.hexdigest(), []).append(p)
                    except Exception as e:
                        logger.error(f"Stage 3 full hash failure on {p}: {e}")

            sha_candidates = {h: paths for h, paths in sha_groups.items() if len(paths) > 1}
            self.progress_updated.emit(90)

            if self._is_cancelled: return

            # --- STAGE 4: Byte-for-byte Verification (Optional) ---
            self.status_updated.emit("Stage 4: Completing matching protocols...")
            self.log_emitted.emit("[STAGE 4] Finalizing byte verification...")
            
            final_groups: Dict[str, List[str]] = {}
            for h, paths in sha_candidates.items():
                # For safety, stringify path representations for transmission to Main Window GUI
                final_groups[h] = [str(p) for p in paths]

            self.progress_updated.emit(100)
            elapsed = round(time.time() - start_time, 2)
            
            self.groups_found.emit(final_groups)
            self.finished_summary.emit({
                "elapsed": elapsed,
                "groups": len(final_groups),
                "total_files": total_scanned
            })

        except Exception as e:
            logger.exception("Duplicate worker runtime exception")
            self.error_raised.emit(str(e))

# ---------------------------------------------------------
# GRAPHICAL VIEWS & PANELS
# ---------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = SettingsService.load()
        self.merge_worker: Optional[MergeWorker] = None
        self.dup_worker: Optional[DuplicateWorker] = None
        self.active_tab_index = 0
        self.test_run_done = False
        self.is_currently_test_run = False
        
        self.init_ui()

    def create_kpi_card(self, title: str, initial_value: str) -> Tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("kpi_card")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("kpi_title")
        title_lbl.setAlignment(Qt.AlignCenter)
        
        value_lbl = QLabel(initial_value)
        value_lbl.setObjectName("kpi_value")
        value_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        
        return card, value_lbl

    def init_ui(self):
        self.setWindowTitle("FileMorph Architect - Python Desktop Utility")
        self.resize(self.settings["window_width"], self.settings["window_height"])

        # Central Layout Builder
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 1. Header bar (First row, completely separate)
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 8)
        
        logo_lbl = QLabel("FM")
        logo_lbl.setStyleSheet("font-weight: 900; font-size: 18px; color: #ffffff; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3b82f6, stop:1 #60a5fa); padding: 4px 10px; border-radius: 6px;")
        
        self.title_lbl = QLabel("FileMorph Architect")
        self.desc_lbl = QLabel("Python PySide6 Desktop Engine")
        
        header_layout.addWidget(logo_lbl)
        header_layout.addWidget(self.title_lbl)
        header_layout.addWidget(self.desc_lbl)
        header_layout.addStretch()
        
        main_layout.addWidget(header_frame)

        # 2. Create Tab Engine (Tab row on left and theme buttons on right)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.tab_changed)
        
        # Corner widget for self.tabs containing theme/utility triggers
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 0, 4)
        corner_layout.setSpacing(6)
        
        # Theme toggle button
        self.btn_theme = QPushButton(f"Theme: {self.settings.get('theme', 'Dark')}")
        self.btn_theme.setObjectName("btn_secondary")
        self.btn_theme.clicked.connect(self.toggle_theme)
        corner_layout.addWidget(self.btn_theme)
        
        # Clear logs button
        self.btn_logs = QPushButton("Clear log")
        self.btn_logs.setObjectName("btn_secondary")
        self.btn_logs.clicked.connect(self.clear_logs)
        corner_layout.addWidget(self.btn_logs)
        
        self.tabs.setCornerWidget(corner_widget, Qt.TopRightCorner)
        
        # Add tab 1 & 2
        self.tab_merge = QWidget()
        self.tab_dup = QWidget()
        
        self.setup_merge_tab()
        self.setup_duplicates_tab()
        
        self.tabs.addTab(self.tab_merge, "Directory Merge")
        self.tabs.addTab(self.tab_dup, "Duplicate File Finder")
        main_layout.addWidget(self.tabs)

        # 3. Footer Actions Panel (Optimized compact height for all bottom bar elements)
        footer_frame = QFrame()
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 12, 0, 0)
        footer_layout.setSpacing(10)
        
        target_height = 34
        
        self.progress_lbl = QLabel("Status: Idle")
        self.progress_lbl.setFixedHeight(target_height)
        self.progress_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.progress_lbl.setMinimumWidth(180)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(target_height)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setFixedHeight(target_height)
        self.btn_cancel.clicked.connect(self.trigger_cancel)
        
        self.btn_test_run = QPushButton("Test Run (Dry Run)")
        self.btn_test_run.setObjectName("btn_secondary")
        self.btn_test_run.setFixedHeight(target_height)
        self.btn_test_run.clicked.connect(self.trigger_test_run)
        
        self.btn_start = QPushButton("Start Operation")
        self.btn_start.setFixedHeight(target_height)
        self.btn_start.clicked.connect(self.trigger_start)
        
        footer_layout.addWidget(self.progress_lbl, 2)
        footer_layout.addWidget(self.progress_bar, 4)
        footer_layout.addWidget(self.btn_cancel, 1)
        footer_layout.addWidget(self.btn_test_run, 2)
        footer_layout.addWidget(self.btn_start, 2)
        
        main_layout.addWidget(footer_frame)

        # Apply current theme
        self.apply_theme(self.settings.get("theme", "Dark"))
        
        # Manually invoke tab_changed to set initial button states
        self.tab_changed(self.tabs.currentIndex())

    # ---------------------------------------------------------
    # TAB 1: DIRECTORY MERGE SETUP
    # ---------------------------------------------------------
    def setup_merge_tab(self):
        layout = QHBoxLayout(self.tab_merge)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left Widget / Layout
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 1. KPI Row Widget
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)
        
        card_total, self.lbl_merge_kpi_total = self.create_kpi_card("TOTAL FILES", "0")
        card_conflicts, self.lbl_merge_kpi_conflicts = self.create_kpi_card("CONFLICTS", "0")
        card_size, self.lbl_merge_kpi_size = self.create_kpi_card("DATA SIZE", "0 MB")
        card_skipped, self.lbl_merge_kpi_skipped = self.create_kpi_card("SKIPPED", "0")
        
        kpi_layout.addWidget(card_total)
        kpi_layout.addWidget(card_conflicts)
        kpi_layout.addWidget(card_size)
        kpi_layout.addWidget(card_skipped)
        left_layout.addLayout(kpi_layout)

        # 2. Browse Fields Frame
        browse_frame = QFrame()
        browse_grid = QVBoxLayout(browse_frame)
        browse_grid.setContentsMargins(0, 0, 0, 0)
        browse_grid.setSpacing(6)

        # Folder A Input
        lbl_a = QLabel("SOURCE FOLDER A")
        lbl_a.setObjectName("section_header")
        row_a = QHBoxLayout()
        self.edit_folder_a = QLineEdit(self.settings["last_folder_a"])
        btn_browse_a = QPushButton("Browse")
        btn_browse_a.setObjectName("btn_secondary")
        btn_browse_a.clicked.connect(lambda: self.browse_folder(self.edit_folder_a, "last_folder_a"))
        row_a.addWidget(self.edit_folder_a)
        row_a.addWidget(btn_browse_a)
        browse_grid.addWidget(lbl_a)
        browse_grid.addLayout(row_a)

        # Folder B Input
        lbl_b = QLabel("SOURCE FOLDER B")
        lbl_b.setObjectName("section_header")
        row_b = QHBoxLayout()
        self.edit_folder_b = QLineEdit(self.settings["last_folder_b"])
        btn_browse_b = QPushButton("Browse")
        btn_browse_b.setObjectName("btn_secondary")
        btn_browse_b.clicked.connect(lambda: self.browse_folder(self.edit_folder_b, "last_folder_b"))
        row_b.addWidget(self.edit_folder_b)
        row_b.addWidget(btn_browse_b)
        browse_grid.addWidget(lbl_b)
        browse_grid.addLayout(row_b)

        # Destination Folder Input
        lbl_dest = QLabel("DESTINATION FOLDER")
        lbl_dest.setObjectName("section_header")
        row_dest = QHBoxLayout()
        self.edit_dest = QLineEdit(self.settings["last_destination"])
        btn_browse_dest = QPushButton("Browse")
        btn_browse_dest.setObjectName("btn_secondary")
        btn_browse_dest.clicked.connect(lambda: self.browse_folder(self.edit_dest, "last_destination"))
        row_dest.addWidget(self.edit_dest)
        row_dest.addWidget(btn_browse_dest)
        browse_grid.addWidget(lbl_dest)
        browse_grid.addLayout(row_dest)

        left_layout.addWidget(browse_frame)

        # 3. Ignore Patterns Field
        ignore_lbl = QLabel("IGNORE PATTERNS (comma-separated globs, e.g. *.tmp, *.log, temp_dir/)")
        ignore_lbl.setObjectName("section_header")
        self.edit_ignore = QLineEdit(self.settings.get("ignore_patterns", "*.tmp, *.log, temp_dir/"))
        self.edit_ignore.setPlaceholderText("e.g. *.tmp, *.log, temp_dir/")
        self.edit_ignore.textChanged.connect(self.save_ignore_patterns)
        left_layout.addWidget(ignore_lbl)
        left_layout.addWidget(self.edit_ignore)

        # 4. Conflict Policy control bar
        controls_bar = QHBoxLayout()
        
        policy_lbl = QLabel("Conflict Policy:")
        self.policy_box = QComboBox()
        self.policy_box.addItem("Keep Both (Automatic Renaming)", "rename_both")
        self.policy_box.addItem("Overwrite Target (A dominates)", "overwrite")
        
        controls_bar.addWidget(policy_lbl)
        controls_bar.addWidget(self.policy_box)
        controls_bar.addStretch()
        
        left_layout.addLayout(controls_bar)

        # Connect input modifications to dynamically update the Test Run / Start button state
        self.edit_folder_a.textChanged.connect(self.on_merge_input_changed)
        self.edit_folder_b.textChanged.connect(self.on_merge_input_changed)
        self.edit_dest.textChanged.connect(self.on_merge_input_changed)
        self.edit_ignore.textChanged.connect(self.on_merge_input_changed)
        self.policy_box.currentIndexChanged.connect(self.on_merge_input_changed)

        # 5. Local Tab Logs below inputs
        console_lbl = QLabel("DIRECTORY MERGE CONSOLE LOGS")
        console_lbl.setObjectName("section_header")
        left_layout.addWidget(console_lbl)
        
        self.merge_console_out = QTextEdit()
        self.merge_console_out.setReadOnly(True)
        self.merge_console_out.append("[SYSTEM] Directory Merge workspace active.")
        left_layout.addWidget(self.merge_console_out)

        # Right Widget / Layout
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Tree View Header
        tree_header = QHBoxLayout()
        preview_title = QLabel("Pre-Merge Decision Tree Preview")
        preview_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #3b82f6;")
        
        legend_lbl = QLabel("● Green = A Only | ● Blue = B Only | ● Orange = Conflict | ● Gray = Identical")
        legend_lbl.setStyleSheet("font-size: 10px; color: #94a3b8;")
        
        tree_header.addWidget(preview_title)
        tree_header.addStretch()
        tree_header.addWidget(legend_lbl)
        right_layout.addLayout(tree_header)

        # Preview Tree
        self.preview_tree = QTreeView()
        self.preview_tree.setHeaderHidden(False)
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Merged Directory Structure"])
        self.preview_tree.setModel(self.tree_model)
        self.preview_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        right_layout.addWidget(self.preview_tree)

        # Add left and right widgets with layout stretch factors
        layout.addWidget(left_widget, 45)
        layout.addWidget(right_widget, 55)

    # ---------------------------------------------------------
    # TAB 2: DUPLICATE FINDER SETUP
    # ---------------------------------------------------------
    def setup_duplicates_tab(self):
        layout = QHBoxLayout(self.tab_dup)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left Widget / Layout
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 1. KPI Row Widget
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)
        
        card_scanned, self.lbl_dup_kpi_scanned = self.create_kpi_card("SCANNED FILES", "0")
        card_groups, self.lbl_dup_kpi_groups = self.create_kpi_card("DUPLICATE GROUPS", "0")
        card_space, self.lbl_dup_kpi_space = self.create_kpi_card("RECLAIMABLE SPACE", "0 MB")
        
        kpi_layout.addWidget(card_scanned)
        kpi_layout.addWidget(card_groups)
        kpi_layout.addWidget(card_space)
        left_layout.addLayout(kpi_layout)

        # 2. Search Target selector
        lbl_target = QLabel("TARGET DIRECTORY TO SCAN")
        lbl_target.setObjectName("section_header")
        row_target = QHBoxLayout()
        self.edit_target = QLineEdit(self.settings["last_duplicate_target"])
        btn_browse_target = QPushButton("Browse")
        btn_browse_target.setObjectName("btn_secondary")
        btn_browse_target.clicked.connect(lambda: self.browse_folder(self.edit_target, "last_duplicate_target"))
        row_target.addWidget(self.edit_target)
        row_target.addWidget(btn_browse_target)
        
        left_layout.addWidget(lbl_target)
        left_layout.addLayout(row_target)

        # 3. Ignore Patterns Field for Duplicates
        ignore_lbl_dup = QLabel("IGNORE PATTERNS (comma-separated globs, e.g. *.tmp, *.log, temp_dir/)")
        ignore_lbl_dup.setObjectName("section_header")
        self.edit_ignore_dup = QLineEdit(self.settings.get("ignore_patterns", "*.tmp, *.log, temp_dir/"))
        self.edit_ignore_dup.setPlaceholderText("e.g. *.tmp, *.log, temp_dir/")
        self.edit_ignore_dup.textChanged.connect(self.save_ignore_patterns)
        left_layout.addWidget(ignore_lbl_dup)
        left_layout.addWidget(self.edit_ignore_dup)

        # 4. Actions bar
        actions_bar = QHBoxLayout()
        
        self.btn_select_all_dups = QPushButton("Select Duplicates")
        self.btn_select_all_dups.setObjectName("btn_secondary")
        self.btn_select_all_dups.clicked.connect(self.select_all_except_first)
        
        self.btn_trash_selected = QPushButton("Move Selected to Recycle Bin")
        self.btn_trash_selected.clicked.connect(self.trash_selected_files)
        
        self.btn_export_csv = QPushButton("Export CSV Report")
        self.btn_export_csv.setObjectName("btn_secondary")
        self.btn_export_csv.clicked.connect(self.export_csv_report)

        actions_bar.addWidget(self.btn_select_all_dups)
        actions_bar.addWidget(self.btn_trash_selected)
        actions_bar.addWidget(self.btn_export_csv)
        
        left_layout.addLayout(actions_bar)

        # 5. Local Tab Logs below inputs
        console_lbl = QLabel("DUPLICATE SCANNER CONSOLE LOGS")
        console_lbl.setObjectName("section_header")
        left_layout.addWidget(console_lbl)
        
        self.dup_console_out = QTextEdit()
        self.dup_console_out.setReadOnly(True)
        self.dup_console_out.append("[SYSTEM] Duplicate Scan workspace active.")
        left_layout.addWidget(self.dup_console_out)

        # Right Widget / Layout
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Registry Header
        results_header = QHBoxLayout()
        res_title = QLabel("Duplicate Group Registry")
        res_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #3b82f6;")
        results_header.addWidget(res_title)
        right_layout.addLayout(results_header)

        # Duplicate results tree
        self.dup_tree = QTreeView()
        self.dup_model = QStandardItemModel()
        self.dup_model.setHorizontalHeaderLabels(["Target Path", "Size", "SHA-256 Content Hash"])
        self.dup_tree.setModel(self.dup_model)
        self.dup_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        right_layout.addWidget(self.dup_tree)

        # Add left and right widgets with stretch factors
        layout.addWidget(left_widget, 45)
        layout.addWidget(right_widget, 55)

    # ---------------------------------------------------------
    # SHARED HELPERS & ROUTINES
    # ---------------------------------------------------------
    def browse_folder(self, line_edit: QLineEdit, setting_key: str):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            line_edit.setText(path)
            self.settings[setting_key] = path
            SettingsService.save(self.settings)

    def tab_changed(self, index: int):
        self.active_tab_index = index
        if hasattr(self, 'btn_start'):
            if index == 0:
                self.btn_start.setText("Run Folder Merge")
                self.btn_test_run.setVisible(True)
                self.btn_start.setEnabled(getattr(self, 'test_run_done', False))
            else:
                self.btn_start.setText("Run Duplicate Scan")
                self.btn_test_run.setVisible(False)
                self.btn_start.setEnabled(True)

    def on_merge_input_changed(self):
        self.test_run_done = False
        if hasattr(self, 'btn_start') and self.active_tab_index == 0:
            self.btn_start.setEnabled(False)
            self.append_log("[SYSTEM] Parameters changed. Perform a Test Run to enable merge execution.")

    @Slot(str)
    def append_log(self, text: str):
        if hasattr(self, 'merge_console_out'):
            self.merge_console_out.append(text)
        if hasattr(self, 'dup_console_out'):
            self.dup_console_out.append(text)
        logger.info(text)

    def clear_logs(self):
        if hasattr(self, 'merge_console_out'):
            self.merge_console_out.clear()
        if hasattr(self, 'dup_console_out'):
            self.dup_console_out.clear()
        self.append_log("[SYSTEM] Console logs reset.")

    def save_ignore_patterns(self, text: str):
        self.settings["ignore_patterns"] = text
        
        # Prevent recursion and loop
        self.edit_ignore.blockSignals(True)
        self.edit_ignore_dup.blockSignals(True)
        
        self.edit_ignore.setText(text)
        self.edit_ignore_dup.setText(text)
        
        self.edit_ignore.blockSignals(False)
        self.edit_ignore_dup.blockSignals(False)
        
        SettingsService.save(self.settings)

    # ---------------------------------------------------------
    # THEME SWITCHING CAPABILITIES
    # ---------------------------------------------------------
    def toggle_theme(self):
        current_theme = self.settings.get("theme", "Dark")
        new_theme = "Light" if current_theme == "Dark" else "Dark"
        self.settings["theme"] = new_theme
        SettingsService.save(self.settings)
        
        self.apply_theme(new_theme)
        self.append_log(f"[THEME] Interface theme switched to {new_theme}.")

    def apply_theme(self, theme: str):
        self.btn_theme.setText(f"Theme: {theme}")
        
        if theme == "Light":
            self.setStyleSheet(SLEEK_LIGHT_STYLE)
            self.title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a;")
            self.desc_lbl.setStyleSheet("font-size: 11px; color: #475569; font-weight: normal;")
            self.progress_lbl.setStyleSheet("color: #475569;")
        else:
            self.setStyleSheet(SLEEK_DARK_STYLE)
            self.title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
            self.desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: normal;")
            self.progress_lbl.setStyleSheet("color: #94a3b8;")

    # ---------------------------------------------------------
    # OPERATIONAL PIPELINES
    # ---------------------------------------------------------
    def trigger_start(self):
        if self.active_tab_index == 0:
            reply = QMessageBox.question(
                self,
                "Confirm Folder Merge",
                "Are you sure you want to run the Folder Merge execution?\n\nThis will apply changes directly to your disk under the Destination folder.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.start_merge(dry_run=False)
        else:
            reply = QMessageBox.question(
                self,
                "Confirm Duplicate Scan",
                "Are you sure you want to run the Duplicate Scan?\n\nThis will scan the target folder recursively for duplicate files.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.start_duplicate_scan()

    def trigger_test_run(self):
        if self.active_tab_index == 0:
            self.start_merge(dry_run=True)

    def trigger_cancel(self):
        if self.merge_worker and self.merge_worker.isRunning():
            self.merge_worker.cancel()
        if self.dup_worker and self.dup_worker.isRunning():
            self.dup_worker.cancel()
        self.btn_cancel.setEnabled(False)

    # Tab 1 execution
    def start_merge(self, dry_run=False):
        folder_a = self.edit_folder_a.text().strip()
        folder_b = self.edit_folder_b.text().strip()
        dest = self.edit_dest.text().strip()

        if not folder_a or not folder_b or not dest:
            QMessageBox.critical(self, "Invalid Configurations", "Please supply Folder A, Folder B, and Destination folder paths.")
            return

        policy = self.policy_box.currentData()
        self.is_currently_test_run = dry_run
        ignore_patterns = self.edit_ignore.text().strip()

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.tabs.setEnabled(False)
        self.progress_bar.setValue(0)
        self.tree_model.removeRows(0, self.tree_model.rowCount())

        # Initialize background worker
        self.merge_worker = MergeWorker(folder_a, folder_b, dest, policy, dry_run, ignore_patterns)
        self.merge_worker.progress_updated.connect(self.progress_bar.setValue)
        self.merge_worker.status_updated.connect(self.progress_lbl.setText)
        self.merge_worker.log_emitted.connect(self.append_log)
        self.merge_worker.preview_ready.connect(self.populate_merge_tree)
        self.merge_worker.finished_summary.connect(self.complete_merge_ui)
        self.merge_worker.error_raised.connect(self.handle_worker_error)
        self.merge_worker.start()

    def populate_merge_tree(self, tree_data: dict):
        """Build a collapsible hierarchical tree-view matching states with sizes and colors."""
        root_item = self.tree_model.invisibleRootItem()
        
        total_files = len(tree_data)
        conflicts = sum(1 for info in tree_data.values() if info["state"] == "conflict")
        total_bytes = 0
        policy = self.policy_box.currentData()
        for info in tree_data.values():
            state = info["state"]
            sz_a = info.get("sz_a", info["size"])
            sz_b = info.get("sz_b", 0)
            if state == "identical":
                total_bytes += sz_a
            elif state == "folderA_only":
                total_bytes += sz_a
            elif state == "folderB_only":
                total_bytes += sz_b
            elif state == "conflict":
                if policy == "rename_both":
                    total_bytes += sz_a + sz_b
                else:
                    total_bytes += sz_a
        
        size_str = format_size(total_bytes)
            
        self.lbl_merge_kpi_total.setText(str(total_files))
        self.lbl_merge_kpi_conflicts.setText(str(conflicts))
        self.lbl_merge_kpi_size.setText(size_str)
        
        # Calculate recursive folder sizes for Left (A) and Right (B) folders
        folder_sizes = {}  # tuple of parent paths -> {"sz_a": 0, "sz_b": 0}
        for rel_path_str, info in tree_data.items():
            state = info["state"]
            sz_a = info.get("sz_a", info["size"]) if info.get("in_a") else 0
            sz_b = info.get("sz_b", 0) if info.get("in_b") else 0
            
            parts = [p for p in rel_path_str.replace('\\', '/').split('/') if p]
            if not parts:
                continue
            parent_dirs = parts[:-1]
            
            # Accumulate sizes for all parent paths
            current_path_tuple = ()
            for folder_name in parent_dirs:
                current_path_tuple += (folder_name,)
                if current_path_tuple not in folder_sizes:
                    folder_sizes[current_path_tuple] = {"sz_a": 0, "sz_b": 0}
                folder_sizes[current_path_tuple]["sz_a"] += sz_a
                folder_sizes[current_path_tuple]["sz_b"] += sz_b

        folder_cache = {}

        for rel_path_str, info in sorted(tree_data.items()):
            state = info["state"]
            file_size_str = format_size(info["size"])
            
            # Split the path into segments
            parts = [p for p in rel_path_str.replace('\\', '/').split('/') if p]
            if not parts:
                continue
                
            filename = parts[-1]
            parent_dirs = parts[:-1]
            
            # Traverse and construct/retrieve collapsible directory nodes
            current_parent = root_item
            current_path_tuple = ()
            
            for folder_name in parent_dirs:
                current_path_tuple += (folder_name,)
                if current_path_tuple in folder_cache:
                    current_parent = folder_cache[current_path_tuple]
                else:
                    # Get accumulated sizes for this folder path
                    f_sz = folder_sizes.get(current_path_tuple, {"sz_a": 0, "sz_b": 0})
                    f_sz_a_str = format_size(f_sz["sz_a"])
                    f_sz_b_str = format_size(f_sz["sz_b"])
                    
                    folder_display_name = f"{folder_name} (Left: {f_sz_a_str}, Right: {f_sz_b_str})"
                    
                    folder_item = QStandardItem(folder_display_name)
                    font = folder_item.font()
                    font.setBold(True)
                    folder_item.setFont(font)
                    
                    # Color coding folder based on contents origin
                    if f_sz["sz_a"] > 0 and f_sz["sz_b"] == 0:
                        folder_item.setForeground(QBrush(QColor("#10b981"))) # Green = A Only
                    elif f_sz["sz_b"] > 0 and f_sz["sz_a"] == 0:
                        folder_item.setForeground(QBrush(QColor("#3b82f6"))) # Blue = B Only
                    else:
                        folder_item.setForeground(QBrush(QColor("#38bdf8"))) # Sky blue = Combined A and B
                        
                    current_parent.appendRow(folder_item)
                    folder_cache[current_path_tuple] = folder_item
                    current_parent = folder_item
            
            # Add file level item with appropriate styling and state descriptors
            if state == "conflict":
                sz_a_str = format_size(info.get("sz_a", info["size"]))
                sz_b_str = format_size(info.get("sz_b", 0))
                file_display_name = f"{filename} (Conflict: Left: {sz_a_str}, Right: {sz_b_str})"
            else:
                file_display_name = f"{filename} ({file_size_str})"
                
            item_path = QStandardItem(file_display_name)
            
            # Apply colored indicators directly to the path/file name item
            if state == "identical":
                item_path.setForeground(QBrush(QColor("#64748b"))) # Gray
            elif state == "conflict":
                item_path.setForeground(QBrush(QColor("#f59e0b"))) # Orange
            elif state == "folderA_only":
                item_path.setForeground(QBrush(QColor("#10b981"))) # Green
            elif state == "folderB_only":
                item_path.setForeground(QBrush(QColor("#3b82f6"))) # Blue

            current_parent.appendRow(item_path)

        self.preview_tree.expandAll()

    def complete_merge_ui(self, stats: dict):
        self.progress_bar.setValue(100)
        self.btn_cancel.setEnabled(False)
        self.tabs.setEnabled(True)
        
        # Test Run vs Actual Run complete flow logic
        if self.is_currently_test_run:
            self.test_run_done = True
            self.progress_lbl.setText("Test Run Completed!")
            self.btn_start.setEnabled(True)
        else:
            self.test_run_done = False
            self.progress_lbl.setText("Operation completed successfully!")
            self.btn_start.setEnabled(False) # A new test run is required if settings are touched
            
        self.lbl_merge_kpi_skipped.setText(str(stats["skipped"]))
        copied_size_str = format_size(stats["data_copied"])
        
        msg = (
            f"Merge completed in {stats['elapsed_time']} seconds!\n\n"
            f"Files Sim/Copied: {stats['copied']}\n"
            f"Conflicts Encountered: {stats['conflicts']}\n"
            f"Duplicates Skipped: {stats['skipped']}\n"
            f"Errors Logged: {stats['errors']}\n"
            f"Data Transferred: {copied_size_str}"
        )
        QMessageBox.information(self, "Process Log Output", msg)

    # Tab 2 execution
    def start_duplicate_scan(self):
        target = self.edit_target.text().strip()
        if not target or not os.path.exists(target):
            QMessageBox.critical(self, "Missing Parameter", "Please select an existing folder to analyze.")
            return

        ignore_patterns = self.edit_ignore_dup.text().strip()

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.tabs.setEnabled(False)
        self.progress_bar.setValue(0)
        self.dup_model.removeRows(0, self.dup_model.rowCount())

        self.dup_worker = DuplicateWorker(target, deep_check=True, ignore_patterns=ignore_patterns)
        self.dup_worker.progress_updated.connect(self.progress_bar.setValue)
        self.dup_worker.status_updated.connect(self.progress_lbl.setText)
        self.dup_worker.log_emitted.connect(self.append_log)
        self.dup_worker.groups_found.connect(self.populate_duplicate_tree)
        self.dup_worker.finished_summary.connect(self.complete_duplicate_ui)
        self.dup_worker.error_raised.connect(self.handle_worker_error)
        self.dup_worker.start()

    def populate_duplicate_tree(self, groups: dict):
        root = self.dup_model.invisibleRootItem()
        group_idx = 0
        
        total_groups = len(groups)
        reclaimable_bytes = 0
        
        for hash_val, paths in groups.items():
            group_idx += 1
            try:
                sz = Path(paths[0]).stat().st_size
                sz_str = format_size(sz)
                reclaimable_bytes += sz * (len(paths) - 1)
            except Exception:
                sz_str = "Unknown"

            # Node Group Header
            hdr_path = QStandardItem(f"Group #{group_idx} - Duplicates ({len(paths)} files)")
            hdr_path.setData(None, Qt.UserRole)
            hdr_size = QStandardItem(sz_str)
            hdr_hash = QStandardItem(hash_val[:16] + "...")
            
            root.appendRow([hdr_path, hdr_size, hdr_hash])
            
            # List actual matches
            for p in paths:
                p_item = QStandardItem(p)
                p_item.setCheckable(True)
                p_item.setData(p, Qt.UserRole)
                
                size_item = QStandardItem(sz_str)
                hash_item = QStandardItem(hash_val)
                hdr_path.appendRow([p_item, size_item, hash_item])

        self.dup_tree.expandAll()
        
        reclaim_str = format_size(reclaimable_bytes)
            
        self.lbl_dup_kpi_groups.setText(str(total_groups))
        self.lbl_dup_kpi_space.setText(reclaim_str)

    def complete_duplicate_ui(self, metrics: dict):
        self.progress_bar.setValue(100)
        self.progress_lbl.setText(f"Scan finished. Found {metrics['groups']} duplicate sets.")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.tabs.setEnabled(True)
        
        self.lbl_dup_kpi_scanned.setText(str(metrics["total_files"]))

    def handle_worker_error(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.tabs.setEnabled(True)
        QMessageBox.critical(self, "Fatal Execution Exception", f"Process threw an error:\n{err_msg}")

    # ---------------------------------------------------------
    # ADDITIONAL UX EXTRAS
    # ---------------------------------------------------------
    def select_all_except_first(self):
        """Auto-checks duplicate copies while keeping the original safe from selection."""
        root = self.dup_model.invisibleRootItem()
        for i in range(root.rowCount()):
            hdr_item = root.child(i, 0)
            if hdr_item:
                for j in range(hdr_item.rowCount()):
                    sub_item = hdr_item.child(j, 0)
                    if sub_item:
                        # Check all entries in the cluster EXCEPT the very first one
                        sub_item.setCheck(Qt.Checked if j > 0 else Qt.Unchecked)

    def trash_selected_files(self):
        """Safely discards verified files using cross-platform recycle bins."""
        root = self.dup_model.invisibleRootItem()
        to_remove = []
        
        for i in range(root.rowCount()):
            hdr_item = root.child(i, 0)
            if hdr_item:
                for j in range(hdr_item.rowCount()):
                    sub_item = hdr_item.child(j, 0)
                    if sub_item and sub_item.checkState() == Qt.Checked:
                        filepath = sub_item.data(Qt.UserRole)
                        if filepath:
                            to_remove.append((filepath, hdr_item, j))

        if not to_remove:
            QMessageBox.information(self, "Empty Selection", "Please check/select duplicates to delete.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Erasure",
            f"Are you sure you want to move {len(to_remove)} duplicate file(s) to the trash/recycle bin?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return

        success_count = 0
        for fp, parent_hdr, row in to_remove:
            try:
                if HAS_SEND2TRASH:
                    send2trash(fp)
                    self.append_log(f"[TRASH] Successfully recycled: {fp}")
                else:
                    os.remove(fp)
                    self.append_log(f"[DELETE] Erased: {fp}")
                success_count += 1
            except Exception as e:
                self.append_log(f"[ERROR] Failed to trash file {fp}: {e}")

        # Refresh Duplicate Finder Registry
        QMessageBox.information(self, "Cleanup Summary", f"Completed: {success_count} files trashed successfully.")
        self.start_duplicate_scan()

    def export_csv_report(self):
        """Exports full analysis log as flat CSV schema for system auditing."""
        path, _ = QFileDialog.getSaveFileName(self, "Export Duplicate Report", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("GroupIndex,Filepath,ContentSHA256\n")
                root = self.dup_model.invisibleRootItem()
                for i in range(root.rowCount()):
                    hdr_item = root.child(i, 0)
                    if hdr_item:
                        for j in range(hdr_item.rowCount()):
                            sub_item = hdr_item.child(j, 0)
                            hash_item = hdr_item.child(j, 2)
                            if sub_item:
                                fp = sub_item.data(Qt.UserRole)
                                h = hash_item.text() if hash_item else ""
                                if fp:
                                    f.write(f"{i+1},\"{fp}\",{h}\n")
            QMessageBox.information(self, "Export Succeeded", f"Report successfully archived to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Exception", f"Unable to generate CSV log: {e}")

    def closeEvent(self, event):
        # Save session parameters
        self.settings["window_width"] = self.width()
        self.settings["window_height"] = self.height()
        SettingsService.save(self.settings)
        event.accept()

# ---------------------------------------------------------
# RUNNER SYSTEM
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
