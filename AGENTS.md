# Architectural Guidelines for Future Coding Agents

Welcome, Agent! This repository contains a production-quality PySide6 desktop tool and a high-fidelity visual simulator. Follow these details to enhance or maintain the code.

---

## 📂 Codebase File Map

- `/desktop_app/main.py`: The complete, fully-featured Python desktop application. Contains MVC/MVVM patterns, asynchronous worker threads, and settings management.
- `/desktop_app/requirements.txt`: System package requirements (`PySide6`, `send2trash`).
- `/src/App.tsx`: High-fidelity interactive web demonstration of the application, featuring custom **Sleek Interface** colors and active **Dry Run** simulation routines.
- `/metadata.json`: Application metadata.

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

### 1. Dry Run Mode
When enabled via `chk_dry_run` or simulated in the web workspace, the `MergeWorker` thread calculates all matching logic (hashes, folder overlays, conflict resolution) but skips the actual read-write file streams, printing all operations with a custom `[DRY RUN]` marker.

### 2. Progressive 4-Stage Scanning (Duplicates)
Scanning up to 500,000+ folders efficiently without memory overflow:
- **Stage 1 (Size Clustering)**: Scans directories recursively and groups items by exact file size. Non-matching sizes are immediately pruned.
- **Stage 2 (Header Hash Check)**: Reads only the first 8 KB block of candidate duplicate files, computing standard MD5 hashes of these chunks to filter mismatches quickly.
- **Stage 3 (Deep SHA-256 Signature)**: Calculates full cryptographic SHA-256 hashes only for files that passed Stage 1 and Stage 2.
- **Stage 4 (Byte-for-Byte Check)**: Conducts strict binary comparison validation before confirming duplicates.

---

## ⚙️ Free-Tier CI/CD GitHub Action Configuration

Create a file at `.github/workflows/build-binaries.yml` with the following configuration to compile Windows, Linux, and macOS standalone binary executables on every push to the `main` branch:

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
          pyinstaller --onefile --windowed --name="MergerDuplicateFinder" desktop_app/main.py

      - name: Upload Build Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.artifact_name }}
          path: dist/
```
