# Architectural Guidelines for Future Coding Agents

Welcome, Agent! This repository contains a production-quality PySide6 desktop tool representing **Directory Tools**—a professional-grade suite combining robust multi-threaded directory merging with high-performance duplicate file scanning. Follow these details to enhance or maintain the code.

---

## 📂 Codebase File Map

- `/desktop_app/main.py`: The complete, fully-featured Python desktop application. Contains robust MVVM/MVC patterns, multi-threaded worker architectures, custom themes, native integrations, and persistence managers.
- `/desktop_app/requirements.txt`: System package requirements (`PySide6`, `send2trash`).

---

## 🚀 PySide6 Local Execution Guide

To run the desktop utility on a computer locally:

1. **Verify Python Installation**: Ensure Python 3.12+ is installed.
2. **Install Package Dependencies**:
   ```bash
   pip install -r desktop_app/requirements.txt
   ```
3. **Launch the GUI Application**:
   ```bash
   python desktop_app/main.py
   ```

---

## 🔍 Core Algorithms & Safety Protocols

### 1. Dry Run / Test Run Workflow
To prevent accidental data loss, the application employs a mandatory **Test Run (Dry Run)** workflow for directory merging:
- Users must click **Test Run (Dry Run)** first.
- The `MergeWorker` thread calculates all matching logic (hashes, folder overlays, conflict resolution) but skips actual write streams.
- A fully collapsible directory preview tree is populated showing the exact merge outline.
- If any input or configuration parameter is edited, the actual execution is disabled, and the user must run another Test Run to review the outline.
- **Safety Dialogs**: Users are explicitly prompted with a confirmation dialog box (`QMessageBox.question`) when initiating either a final folder merge execution or a duplicate file scan.

### 2. Collapsible Hierarchical Tree Preview & Color Coding
The folder merge preview is presented in a highly organized, single-column collapsible tree view (`QTreeView`). This provides clear visual grouping of files into directories:
- **Left/Right Folder Size Aggregations**:
  - Every parent directory node dynamically displays the exact aggregate size of all files contained within it from both folders: e.g., `folder_name (Left: 1.2 MB, Right: 340.0 KB)`.
  - Sizes are formatted elegantly (`Bytes`, `KB`, `MB`, `GB`, `TB`) based on actual file size.
- **Visual Origin Indicators & Theme Colors**:
  - The traditional "Overlay State" and "Action Decision" columns have been replaced with direct visual styling.
  - **Identical Files**: Styled in muted Gray (`#64748b`) indicating clean consolidation.
  - **A-Only Files**: Styled in vibrant Green (`#10b981`) indicating incorporation from Folder A.
  - **B-Only Files**: Styled in deep Blue (`#3b82f6`) indicating incorporation from Folder B.
  - **Conflict Files**: Styled in striking Orange (`#f59e0b`), listing separate Left and Right sizes: e.g., `file.txt (Conflict: Left: 5.0 KB, Right: 6.2 KB)`.
  - **Folders**: Directories are colored automatically according to their contents' origins: Green if only containing Left items, Blue if only containing Right items, and Sky Blue (`#38bdf8`) if containing a hybrid blend of both.

### 3. Smart Merge Size Estimations
The calculated total size of the final merged folder dynamically reflects the chosen **Conflict Resolution Policy**:
- **Keep Both**: Adds up both Left and Right candidate sizes for conflicting files.
- **Overwrite / Left Dominates**: Resolves conflict sizes by counting only the Left (Folder A) variant of conflicting files.

### 4. Progressive 4-Stage Scanning (Duplicates)
Scanning up to 500,000+ folders efficiently without memory overflow:
- **Stage 1 (Size Clustering)**: Scans directories recursively and groups items by exact file size. Non-matching sizes are immediately pruned.
- **Stage 2 (Header Hash Check)**: Reads only the first 8 KB block of candidate duplicate files, computing standard MD5 hashes of these chunks to filter mismatches quickly.
- **Stage 3 (Deep SHA-256 Signature)**: Calculates full cryptographic SHA-256 hashes only for files that passed Stage 1 and Stage 2.
- **Stage 4 (Byte-for-Byte Check)**: Conducts strict binary comparison validation before confirming duplicates.

---

## 🎨 New Architectural Enhancements & Features

### 1. Application Name & Native Brand Integration
- The application is formally titled **Directory Tools** across all view components, title bars, and subtitles.
- Features a stylized logo header label (**DT**).
- Implements direct integration with native operating system standard icons (`QStyle.SP_DirIcon`), presenting a familiar, high-quality desktop integration out-of-the-box on Windows, Linux, and macOS.
- Launches automatically in maximized mode (`showMaximized`) to provide maximum screen real-estate for comparing directory structures and duplicate lists.

### 2. System-Adaptive Theme Engine
- By default, the application queries the system's color palette during initialization.
- Uses a background color lightness heuristic (`lightness < 128`) to automatically configure a **Dark Theme** or a **Light Theme** matching the user's OS preference.
- Safely falls back to a clean, high-contrast **Light Theme** if the system palette is light or cannot be programmatically verified.
- Maintains user choice via interactive top-right corner theme-toggle persistence.

### 3. Restructured Duplicates Registry & Multi-Column Sorting
- The duplicate list structure is redefined using three highly readable columns: **Path**, **File Name**, and **Size**.
- The full file path is placed in Column 0, the specific file name in Column 1, and its human-readable formatted size in Column 2.
- Interactive sorting is fully supported across all columns: clicking column headers dynamically sorts duplicate rows alphabetically (by Name or Path) or numerically (by Size).
- Proper numeric sorting for sizes is achieved by backing the visible formatted string size items with raw byte size integers inside the custom `Qt.SortRole` property.
- Cryptographic SHA-256 hashes are mapped behind-the-scenes inside invisible `Qt.UserRole + 1` data slots to prevent UI clutter while fully preserving the professional CSV Audit Log export.

### 4. High-Contrast Duplicate Highlight Rules
- When a duplicate group contains more than one duplicate copy (i.e., `total copies > 2`, meaning at least 3 instances are present on disk), the application highlights all files in that specific group.
- Highlighted items are rendered with a soft, semi-transparent colored background and styled with bold display typography to draw immediate user attention to high-density waste.

---

## ⚙️ Free-Tier CI/CD GitHub Action Configuration

A GitHub Actions workflow is pre-configured at `.github/workflows/build-binaries.yml` to compile Windows, Linux, and macOS standalone binary executables on every push to the `main` branch:

```yaml
name: Build Desktop Executables

on:
  push:
    branches:
      - main

jobs:
  build:
    name: Build Standalone Executables
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        include:
          - os: ubuntu-latest
            artifact_name: merger-duplicate-finder-linux
          - os: windows-latest
            artifact_name: merger-duplicate-finder-windows.exe
          - os: macos-latest
            artifact_name: merger-duplicate-finder-macos

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-level: '3.12'

      - name: Install System Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install PySide6 send2trash pyinstaller

      - name: Package Application with PyInstaller
        run: |
          pyinstaller --onefile --windowed --name="DirectoryTools" desktop_app/main.py

      - name: Upload Build Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.artifact_name }}
          path: dist/
```
