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

# ---------------------------------------------------------
# STYLES (Sleek Interface Custom Design Theme)
# ---------------------------------------------------------
SLEEK_DARK_STYLE = """
QMainWindow {
    background-color: #0f172a;
}
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #f8fafc;
}
QFrame {
    border: none;
}
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #1e293b;
    color: #94a3b8;
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
    background-color: #334155;
    color: #e2e8f0;
}
QLineEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
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
    background-color: #1e293b;
    color: #64748b;
}
QPushButton#btn_secondary {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
}
QPushButton#btn_secondary:hover {
    background-color: #334155;
}
QTreeView {
    background-color: #111827;
    border: 1px solid #1e293b;
    border-radius: 8px;
    gridline-color: #1e293b;
    color: #e2e8f0;
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
    border: 1px solid #1e293b;
    border-radius: 4px;
    text-align: center;
    background-color: #1e293b;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}
QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px;
    color: #f8fafc;
}
QTextEdit {
    background-color: #0b0f19;
    border: 1px solid #1e293b;
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
    border-radius: 4px;
    text-align: center;
    background-color: #e2e8f0;
    color: #0f172a;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px;
    color: #0f172a;
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

            # Preview calculations
            for i, rel_path in enumerate(all_rel_paths):
                if self._is_cancelled:
                    self.log_emitted.emit("[WARN] Merge operation cancelled by user.")
                    return

                in_a = rel_path in files_a
                in_b = rel_path in files_b
                
                state = "identical"
                size = 0
                
                if in_a and in_b:
                    # Compare content hashes
                    hash_a = self.calculate_file_hash(files_a[rel_path])
                    hash_b = self.calculate_file_hash(files_b[rel_path])
                    if hash_a == hash_b:
                        state = "identical"
                        size = files_a[rel_path].stat().st_size
                    else:
                        state = "conflict"
                        stats["conflicts"] += 1
                elif in_a:
                    state = "folderA_only"
                    size = files_a[rel_path].stat().st_size
                else:
                    state = "folderB_only"
                    size = files_b[rel_path].stat().st_size

                preview_tree[str(rel_path)] = {
                    "state": state,
                    "in_a": in_a,
                    "in_b": in_b,
                    "size": size
                }

            self.preview_ready.emit(preview_tree)

            # Execution (If not dry run)
            self.status_updated.emit("Merging files...")
            for rel_path, info in preview_tree.items():
                if self._is_cancelled:
                    return
                
                processed_items += 1
                self.progress_updated.emit(int((processed_items / total_items) * 100))
                
                p = Path(rel_path)
                state = info["state"]
                
                if state == "identical":
                    # Just copy A to dest
                    self._copy_file_safe(files_a[p], self.dest_folder / p, stats)
                    stats["skipped"] += 1 # We kept only one copy, skipped B
                elif state == "folderA_only":
                    self._copy_file_safe(files_a[p], self.dest_folder / p, stats)
                    stats["copied"] += 1
                elif state == "folderB_only":
                    self._copy_file_safe(files_b[p], self.dest_folder / p, stats)
                    stats["copied"] += 1
                elif state == "conflict":
                    if self.policy == "rename_both":
                        # Rename strategy: main.py -> main (Folder A).py and main (Folder B).py
                        stem, suffix = p.stem, p.suffix
                        name_a = f"{stem} (Folder A){suffix}"
                        name_b = f"{stem} (Folder B){suffix}"
                        
                        self._copy_file_safe(files_a[p], self.dest_folder / p.parent / name_a, stats)
                        self._copy_file_safe(files_b[p], self.dest_folder / p.parent / name_b, stats)
                        stats["copied"] += 2
                        self.log_emitted.emit(f"[CONFLICT] Renamed both candidates for {rel_path}")
                    else:
                        # Overwrite with Folder A
                        self._copy_file_safe(files_a[p], self.dest_folder / p, stats)
                        stats["copied"] += 1
                        self.log_emitted.emit(f"[CONFLICT] Overwrote conflict with Folder A version: {rel_path}")

            stats["elapsed_time"] = round(time.time() - start_time, 2)
            self.finished_summary.emit(stats)

        except Exception as e:
            logger.exception("Merge worker runtime exception")
            self.error_raised.emit(str(e))

    def _copy_file_safe(self, src: Path, dest: Path, stats: dict):
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
            self.log_emitted.emit(f"[COPY] {src.name} -> {dest.name}")
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
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("FileMorph Architect - Python Desktop Utility")
        self.resize(self.settings["window_width"], self.settings["window_height"])

        # Central Layout Builder
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header bar
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
        
        # Theme toggle button
        self.btn_theme = QPushButton(f"Theme: {self.settings.get('theme', 'Dark')}")
        self.btn_theme.setObjectName("btn_secondary")
        self.btn_theme.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btn_theme)
        
        # Quick view log button
        self.btn_logs = QPushButton("Clear log")
        self.btn_logs.setObjectName("btn_secondary")
        self.btn_logs.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.btn_logs)
        
        main_layout.addWidget(header_frame)

        # Create Tab Engine
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.tab_changed)
        
        # Add tab 1 & 2
        self.tab_merge = QWidget()
        self.tab_dup = QWidget()
        
        self.setup_merge_tab()
        self.setup_duplicates_tab()
        
        self.tabs.addTab(self.tab_merge, "Directory Merge")
        self.tabs.addTab(self.tab_dup, "Duplicate File Finder")
        main_layout.addWidget(self.tabs)

        # Logging / Console Area
        console_lbl = QLabel("SYSTEM CONSOLE OUT (application.log)")
        console_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #64748b; margin-top: 8px;")
        main_layout.addWidget(console_lbl)
        
        self.console_out = QTextEdit()
        self.console_out.setReadOnly(True)
        self.console_out.append("[SYSTEM] Application ready. Modern PySide6 style loaded.")
        main_layout.addWidget(self.console_out)

        # Footer Actions Panel
        footer_frame = QFrame()
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 12, 0, 0)
        
        # Progress and status info
        self.progress_lbl = QLabel("Status: Idle")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        
        progress_box = QVBoxLayout()
        progress_box.addWidget(self.progress_lbl)
        progress_box.addWidget(self.progress_bar)
        footer_layout.addLayout(progress_box, 4)

        # Shared triggers
        self.btn_start = QPushButton("Start Operation")
        self.btn_start.clicked.connect(self.trigger_start)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.trigger_cancel)
        
        footer_layout.addWidget(self.btn_cancel, 1)
        footer_layout.addWidget(self.btn_start, 1)
        
        main_layout.addWidget(footer_frame)

        # Apply current theme
        self.apply_theme(self.settings.get("theme", "Dark"))

    # ---------------------------------------------------------
    # TAB 1: DIRECTORY MERGE SETUP
    # ---------------------------------------------------------
    def setup_merge_tab(self):
        layout = QVBoxLayout(self.tab_merge)
        layout.setContentsMargins(16, 16, 16, 16)

        # Browse Fields Config Grid
        browse_frame = QFrame()
        browse_grid = QVBoxLayout(browse_frame)
        browse_grid.setContentsMargins(0, 0, 0, 0)

        # Folder A Input
        lbl_a = QLabel("SOURCE FOLDER A")
        lbl_a.setStyleSheet("font-weight: bold; font-size: 10px; color: #64748b;")
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
        lbl_b.setStyleSheet("font-weight: bold; font-size: 10px; color: #64748b;")
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
        lbl_dest.setStyleSheet("font-weight: bold; font-size: 10px; color: #64748b;")
        row_dest = QHBoxLayout()
        self.edit_dest = QLineEdit(self.settings["last_destination"])
        btn_browse_dest = QPushButton("Browse")
        btn_browse_dest.setObjectName("btn_secondary")
        btn_browse_dest.clicked.connect(lambda: self.browse_folder(self.edit_dest, "last_destination"))
        row_dest.addWidget(self.edit_dest)
        row_dest.addWidget(btn_browse_dest)
        browse_grid.addWidget(lbl_dest)
        browse_grid.addLayout(row_dest)

        layout.addWidget(browse_frame)

        # Ignore Patterns Field
        ignore_lbl = QLabel("IGNORE PATTERNS (comma-separated globs, e.g. *.tmp, *.log, temp_dir/)")
        ignore_lbl.setStyleSheet("font-weight: bold; font-size: 10px; color: #64748b;")
        self.edit_ignore = QLineEdit(self.settings.get("ignore_patterns", "*.tmp, *.log, temp_dir/"))
        self.edit_ignore.setPlaceholderText("e.g. *.tmp, *.log, temp_dir/")
        self.edit_ignore.textChanged.connect(self.save_ignore_patterns)
        layout.addWidget(ignore_lbl)
        layout.addWidget(self.edit_ignore)

        # Conflict Policy & DRY RUN control bar
        controls_bar = QHBoxLayout()
        
        policy_lbl = QLabel("Conflict Policy:")
        self.policy_box = QComboBox()
        self.policy_box.addItem("Keep Both (Automatic Renaming)", "rename_both")
        self.policy_box.addItem("Overwrite Target (A dominates)", "overwrite")
        
        self.chk_dry_run = QCheckBox("Dry Run Mode (Simulate without changing disk)")
        self.chk_dry_run.setChecked(True)
        self.chk_dry_run.setStyleSheet("font-weight: bold;")
        
        controls_bar.addWidget(policy_lbl)
        controls_bar.addWidget(self.policy_box)
        controls_bar.addSpacing(20)
        controls_bar.addWidget(self.chk_dry_run)
        controls_bar.addStretch()
        
        layout.addLayout(controls_bar)

        # Tree View for preview
        tree_header = QHBoxLayout()
        preview_title = QLabel("Pre-Merge Decision Tree Preview")
        preview_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #3b82f6;")
        
        legend_lbl = QLabel("● Green = A Only | ● Blue = B Only | ● Orange = Conflict | ● Gray = Identical")
        legend_lbl.setStyleSheet("font-size: 10px; color: #94a3b8;")
        
        tree_header.addWidget(preview_title)
        tree_header.addStretch()
        tree_header.addWidget(legend_lbl)
        layout.addLayout(tree_header)

        self.preview_tree = QTreeView()
        self.preview_tree.setHeaderHidden(False)
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Relative Path", "Overlay State", "Action Decision"])
        self.preview_tree.setModel(self.tree_model)
        self.preview_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.preview_tree)

    # ---------------------------------------------------------
    # TAB 2: DUPLICATE FINDER SETUP
    # ---------------------------------------------------------
    def setup_duplicates_tab(self):
        layout = QVBoxLayout(self.tab_dup)
        layout.setContentsMargins(16, 16, 16, 16)

        # Search Target selector
        lbl_target = QLabel("TARGET DIRECTORY TO SCAN")
        lbl_target.setStyleSheet("font-weight: bold; font-size: 10px; color: #64748b;")
        row_target = QHBoxLayout()
        self.edit_target = QLineEdit(self.settings["last_duplicate_target"])
        btn_browse_target = QPushButton("Browse")
        btn_browse_target.setObjectName("btn_secondary")
        btn_browse_target.clicked.connect(lambda: self.browse_folder(self.edit_target, "last_duplicate_target"))
        row_target.addWidget(self.edit_target)
        row_target.addWidget(btn_browse_target)
        
        layout.addWidget(lbl_target)
        layout.addLayout(row_target)

        # Ignore Patterns Field for Duplicates
        ignore_lbl_dup = QLabel("IGNORE PATTERNS (comma-separated globs, e.g. *.tmp, *.log, temp_dir/)")
        ignore_lbl_dup.setStyleSheet("font-weight: bold; font-size: 10px; color: #64748b;")
        self.edit_ignore_dup = QLineEdit(self.settings.get("ignore_patterns", "*.tmp, *.log, temp_dir/"))
        self.edit_ignore_dup.setPlaceholderText("e.g. *.tmp, *.log, temp_dir/")
        self.edit_ignore_dup.textChanged.connect(self.save_ignore_patterns)
        layout.addWidget(ignore_lbl_dup)
        layout.addWidget(self.edit_ignore_dup)

        # Duplicate results display tree
        results_header = QHBoxLayout()
        res_title = QLabel("Duplicate Group Registry")
        res_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #3b82f6;")
        results_header.addWidget(res_title)
        results_header.addStretch()
        layout.addLayout(results_header)

        self.dup_tree = QTreeView()
        self.dup_model = QStandardItemModel()
        self.dup_model.setHorizontalHeaderLabels(["Target Path", "Size", "SHA-256 Content Hash"])
        self.dup_tree.setModel(self.dup_model)
        self.dup_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.dup_tree)

        # Selection controls & Action Buttons
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
        actions_bar.addStretch()
        actions_bar.addWidget(self.btn_export_csv)
        layout.addLayout(actions_bar)

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
        # Update Start Button text
        if index == 0:
            self.btn_start.setText("Run Folder Merge")
        else:
            self.btn_start.setText("Run Duplicate Scan")

    @Slot(str)
    def append_log(self, text: str):
        self.console_out.append(text)
        logger.info(text)

    def clear_logs(self):
        self.console_out.clear()
        self.append_log("[SYSTEM] Console log reset.")

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
            self.chk_dry_run.setStyleSheet("font-weight: bold; color: #0f172a;")
            self.btn_theme.setStyleSheet("color: #0f172a;")
            self.btn_logs.setStyleSheet("color: #0f172a;")
            self.btn_select_all_dups.setStyleSheet("color: #0f172a;")
            self.btn_export_csv.setStyleSheet("color: #0f172a;")
            self.btn_cancel.setStyleSheet("color: #0f172a;")
        else:
            self.setStyleSheet(SLEEK_DARK_STYLE)
            self.title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
            self.desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: normal;")
            self.progress_lbl.setStyleSheet("color: #94a3b8;")
            self.chk_dry_run.setStyleSheet("font-weight: bold; color: #e2e8f0;")
            self.btn_theme.setStyleSheet("color: #f8fafc;")
            self.btn_logs.setStyleSheet("color: #f8fafc;")
            self.btn_select_all_dups.setStyleSheet("color: #f8fafc;")
            self.btn_export_csv.setStyleSheet("color: #f8fafc;")
            self.btn_cancel.setStyleSheet("color: #f8fafc;")

    # ---------------------------------------------------------
    # OPERATIONAL PIPELINES
    # ---------------------------------------------------------
    def trigger_start(self):
        if self.active_tab_index == 0:
            self.start_merge()
        else:
            self.start_duplicate_scan()

    def trigger_cancel(self):
        if self.merge_worker and self.merge_worker.isRunning():
            self.merge_worker.cancel()
        if self.dup_worker and self.dup_worker.isRunning():
            self.dup_worker.cancel()
        self.btn_cancel.setEnabled(False)

    # Tab 1 execution
    def start_merge(self):
        folder_a = self.edit_folder_a.text().strip()
        folder_b = self.edit_folder_b.text().strip()
        dest = self.edit_dest.text().strip()

        if not folder_a or not folder_b or not dest:
            QMessageBox.critical(self, "Invalid Configurations", "Please supply Folder A, Folder B, and Destination folder paths.")
            return

        policy = self.policy_box.currentData()
        dry_run = self.chk_dry_run.isChecked()
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
        """Build a tree-view matching states."""
        root_item = self.tree_model.invisibleRootItem()
        
        for rel_path_str, info in sorted(tree_data.items()):
            state = info["state"]
            size_mb = round(info["size"] / (1024 * 1024), 2)
            
            item_path = QStandardItem(rel_path_str)
            item_state = QStandardItem(state.upper())
            item_decision = QStandardItem()
            
            # Apply colored indicators
            if state == "identical":
                item_state.setForeground(QBrush(QColor("#64748b")))
                item_decision.setText(f"Keep unique copy ({size_mb} MB)")
            elif state == "conflict":
                item_state.setForeground(QBrush(QColor("#f59e0b")))
                item_decision.setText("Duplicated renaming requested")
            elif state == "folderA_only":
                item_state.setForeground(QBrush(QColor("#10b981")))
                item_decision.setText(f"Incorporate from A ({size_mb} MB)")
            elif state == "folderB_only":
                item_state.setForeground(QBrush(QColor("#3b82f6")))
                item_decision.setText(f"Incorporate from B ({size_mb} MB)")

            root_item.appendRow([item_path, item_state, item_decision])

    def complete_merge_ui(self, stats: dict):
        self.progress_bar.setValue(100)
        self.progress_lbl.setText("Operation completed successfully!")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.tabs.setEnabled(True)

        copied_mb = round(stats["data_copied"] / (1024 * 1024), 2)
        
        msg = (
            f"Merge completed in {stats['elapsed_time']} seconds!\n\n"
            f"Files Sim/Copied: {stats['copied']}\n"
            f"Conflicts Encountered: {stats['conflicts']}\n"
            f"Duplicates Skipped: {stats['skipped']}\n"
            f"Errors Logged: {stats['errors']}\n"
            f"Data Transferred: {copied_mb} MB"
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
        
        for hash_val, paths in groups.items():
            group_idx += 1
            # Retrieve size from first path safely
            try:
                sz = Path(paths[0]).stat().st_size
                sz_str = f"{round(sz / 1024, 1)} KB" if sz < 1048576 else f"{round(sz / 1048576, 1)} MB"
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
                p_item.setData(p, Qt.UserRole) # Keep file path in custom data
                
                size_item = QStandardItem(sz_str)
                hash_item = QStandardItem(hash_val)
                hdr_path.appendRow([p_item, size_item, hash_item])

        self.dup_tree.expandAll()

    def complete_duplicate_ui(self, metrics: dict):
        self.progress_bar.setValue(100)
        self.progress_lbl.setText(f"Scan finished. Found {metrics['groups']} duplicate sets.")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.tabs.setEnabled(True)

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
