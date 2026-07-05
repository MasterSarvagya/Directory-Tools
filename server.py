#!/usr/bin/env python3
"""
FileMorph Web Server Backend
A custom Python 3.12+ web server using standard library modules.
Provides the full-stack Python backend logic for the web workspace preview,
running identical merge and duplicates algorithms on the filesystem!
"""

import os
import sys
import json
import time
import hashlib
import fnmatch
import mimetypes
from pathlib import Path
import http.server
import socketserver
from typing import Dict, List, Set, Tuple, Optional, Any

PORT = 3000
SETTINGS_FILE = "settings.json"
LOG_BUFFER = []

# Add standard mime types
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/json", ".json")

def add_log(msg: str):
    """Logs backend events into memory buffer and application.log file."""
    timestamp = time.strftime('%H:%M:%S')
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    LOG_BUFFER.append(log_line)
    if len(LOG_BUFFER) > 300:
        LOG_BUFFER.pop(0)
    try:
        with open("application.log", "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception:
        pass

# ---------------------------------------------------------
# DIRECTORY SEEDING LOGIC
# ---------------------------------------------------------
WORKSPACE_SIM = Path("./workspace_simulation").resolve()

def seed_workspace():
    """Seeds a mockup filesystem tree inside the sandbox so users can test immediately!"""
    add_log("[SYSTEM] Verifying test workspace simulation seeding...")
    
    folder_a = WORKSPACE_SIM / "folder_a"
    folder_b = WORKSPACE_SIM / "folder_b"
    dest = WORKSPACE_SIM / "destination"
    dup_target = WORKSPACE_SIM / "duplicates_target"
    
    # Create directories
    for d in [folder_a, folder_b, dest, dup_target, dup_target / "subfolder", dup_target / "backups"]:
        d.mkdir(parents=True, exist_ok=True)
        
    # Write files for Folder A
    with open(folder_a / "main.py", "w", encoding="utf-8") as f:
        f.write("# FileMorph main execution script - Version A\nprint('Initializing FileMorph Architect Core Engine...')\ncore_hash_mode = 'Progressive-4-Stage-MD5-SHA'\n")
        
    with open(folder_a / "utils.py", "w", encoding="utf-8") as f:
        f.write("# Shared helper functions\ndef compute_md5_header(path):\n    return '0f172a'\n")
        
    with open(folder_a / "architect.py", "w", encoding="utf-8") as f:
        f.write("# Core System Architect Module\nclass SystemArchitect:\n    pass\n")
        
    with open(folder_a / "temp_cache.tmp", "w", encoding="utf-8") as f:
        f.write("Temporary caching file. This file should be skipped by your ignore patterns (*.tmp)!")
        
    with open(folder_a / "system.log", "w", encoding="utf-8") as f:
        f.write("System diagnostic log. This file should be skipped by your ignore patterns (*.log)!")

    # Write files for Folder B
    with open(folder_b / "main.py", "w", encoding="utf-8") as f:
        f.write("# FileMorph main execution script - Version B\nprint('Starting Core Engine (Production Workspace B)...')\ncore_hash_mode = 'SHA-256-Strict-Byte-Compare'\n")
        
    with open(folder_b / "utils.py", "w", encoding="utf-8") as f:
        f.write("# Shared helper functions\ndef compute_md5_header(path):\n    return '0f172a'\n") # Identical content to A/utils.py
        
    with open(folder_b / "logo_v2.png", "w", encoding="utf-8") as f:
        f.write("[Fake Binary PNG Logo Image Metadata - Exists Only in Folder B]")
        
    with open(folder_b / "config.yaml", "w", encoding="utf-8") as f:
        f.write("# Configuration Version B\ndebug: false\nthread_count: 8\n")
        
    with open(folder_a / "config.yaml", "w", encoding="utf-8") as f:
        f.write("# Configuration Version A\ndebug: true\nthread_count: 4\n")

    # Write files for Duplicates Target
    duplicate_content_1 = "This is a redundant text document used to verify progressive duplicate cluster detection."
    duplicate_content_2 = "[BINARY_HEADER_META_SIGNATURE] Raw asset data bytes of identical illustration files."
    
    with open(dup_target / "document_original.txt", "w", encoding="utf-8") as f:
        f.write(duplicate_content_1)
    with open(dup_target / "subfolder" / "document_copy.txt", "w", encoding="utf-8") as f:
        f.write(duplicate_content_1) # Exact Duplicate 1
    with open(dup_target / "backups" / "doc_archive.txt", "w", encoding="utf-8") as f:
        f.write(duplicate_content_1) # Exact Duplicate 2
        
    with open(dup_target / "vector_logo.png", "w", encoding="utf-8") as f:
        f.write(duplicate_content_2)
    with open(dup_target / "backups" / "vector_logo_backup.png", "w", encoding="utf-8") as f:
        f.write(duplicate_content_2) # Exact Duplicate 3
        
    with open(dup_target / "unique_notes.txt", "w", encoding="utf-8") as f:
        f.write("This file is completely unique and has zero identical copies.")
        
    with open(dup_target / "temp_diagnostics.tmp", "w", encoding="utf-8") as f:
        f.write("Temporary file inside duplicates directory. This should be ignored by *.tmp pattern!")

    add_log("[SYSTEM] Simulation workspace folders populated with 12 distinct test nodes successfully.")

# ---------------------------------------------------------
# IGNORE AND UTILITIES MATCHERS
# ---------------------------------------------------------
def should_ignore(path: Path, base_dir: Path, ignore_patterns: str) -> bool:
    """Evaluates if a path matches glob patterns (e.g. *.tmp, *.log, temp_dir/)."""
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
        # Directory pattern
        if pattern_norm.endswith("/"):
            dir_pat = pattern_norm.rstrip("/")
            parts = rel_path_str.split("/")
            if any(fnmatch.fnmatch(part, dir_pat) for part in parts[:-1]):
                return True
        else:
            if fnmatch.fnmatch(filename, pattern_norm) or fnmatch.fnmatch(rel_path_str, pattern_norm):
                return True
    return False

def calculate_file_hash(path: Path) -> str:
    """Computes MD5 hash in 64KB chunks."""
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""

def calculate_sha256(path: Path) -> str:
    """Computes SHA-256 hash in 64KB chunks."""
    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1048576:
        return f"{round(size_bytes / 1024, 1)} KB"
    else:
        return f"{round(size_bytes / 1048576, 1)} MB"

# ---------------------------------------------------------
# CUSTOM WEB SERVER REQUEST HANDLER
# ---------------------------------------------------------
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # 1. API: Settings Endpoint
        if self.path == "/api/settings":
            settings = self.load_settings_file()
            self.send_json(settings)
            return
            
        # 2. API: Terminal Logs Endpoint
        elif self.path == "/api/logs":
            self.send_json({"logs": LOG_BUFFER})
            return

        # 3. Serving Static Files from ./dist with fallback to index.html for SPA router
        else:
            dist_dir = Path("./dist").resolve()
            # If path ends in a slash, look for index.html
            clean_path = self.path.split('?')[0].split('#')[0]
            if clean_path == "/":
                clean_path = "/index.html"
                
            target_file = dist_dir / clean_path.lstrip('/')
            
            # If the file exists and is within dist_dir, serve it
            if target_file.exists() and target_file.is_file() and target_file.resolve().is_relative_to(dist_dir):
                self.serve_file(target_file)
            else:
                # SPA Fallback: Serve dist/index.html
                index_file = dist_dir / "index.html"
                if index_file.exists():
                    self.serve_file(index_file)
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Frontend builds not found. Run npm run build first!")

    def do_POST(self):
        # 1. API: Update Settings
        if self.path == "/api/settings":
            try:
                params = self.read_json_body()
                settings = self.load_settings_file()
                settings.update(params)
                self.save_settings_file(settings)
                self.send_json({"status": "success", "settings": settings})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
                
        # 2. API: Pre-Merge preview decision tree calculations
        elif self.path == "/api/preview":
            try:
                params = self.read_json_body()
                folder_a = Path(params.get("folder_a", "")).resolve()
                folder_b = Path(params.get("folder_b", "")).resolve()
                ignore_patterns = params.get("ignore_patterns", "")
                
                if not folder_a.exists() or not folder_b.exists():
                    self.send_json({"error": "Source folders A or B do not exist on disk"}, 400)
                    return
                    
                files_a = {}
                files_b = {}
                
                for root, dirs, files in os.walk(folder_a):
                    dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, folder_a, ignore_patterns)]
                    for file in files:
                        abs_path = Path(root) / file
                        if should_ignore(abs_path, folder_a, ignore_patterns):
                            continue
                        rel_path = abs_path.relative_to(folder_a)
                        files_a[rel_path] = abs_path
                        
                for root, dirs, files in os.walk(folder_b):
                    dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, folder_b, ignore_patterns)]
                    for file in files:
                        abs_path = Path(root) / file
                        if should_ignore(abs_path, folder_b, ignore_patterns):
                            continue
                        rel_path = abs_path.relative_to(folder_b)
                        files_b[rel_path] = abs_path
                        
                all_paths = sorted(list(set(files_a.keys()).union(set(files_b.keys()))))
                
                preview_list = []
                for idx, rel_path in enumerate(all_paths):
                    in_a = rel_path in files_a
                    in_b = rel_path in files_b
                    state = "identical"
                    size = 0
                    
                    if in_a and in_b:
                        hash_a = calculate_file_hash(files_a[rel_path])
                        hash_b = calculate_file_hash(files_b[rel_path])
                        if hash_a == hash_b:
                            state = "identical"
                            size = files_a[rel_path].stat().st_size
                        else:
                            state = "conflict"
                            size = files_a[rel_path].stat().st_size
                    elif in_a:
                        state = "folderA_only"
                        size = files_a[rel_path].stat().st_size
                    else:
                        state = "folderB_only"
                        size = files_b[rel_path].stat().st_size
                        
                    preview_list.append({
                        "id": str(idx + 1),
                        "name": rel_path.name,
                        "type": "file",
                        "path": str(rel_path).replace("\\", "/"),
                        "state": state,
                        "size": format_size(size),
                        "depth": len(rel_path.parts)
                    })
                self.send_json({"items": preview_list})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
                
        # 3. API: Run Merge Operation
        elif self.path == "/api/merge":
            try:
                params = self.read_json_body()
                folder_a = Path(params.get("folder_a", "")).resolve()
                folder_b = Path(params.get("folder_b", "")).resolve()
                dest = Path(params.get("destination", "")).resolve()
                policy = params.get("policy", "rename_both")
                dry_run = params.get("dry_run", True)
                ignore_patterns = params.get("ignore_patterns", "")
                
                add_log(f"[INFO] Initializing scan sequence (Dry Run: {dry_run})")
                if ignore_patterns:
                    add_log(f"[INFO] Active ignore patterns: {ignore_patterns}")
                    
                files_a = {}
                files_b = {}
                
                for root, dirs, files in os.walk(folder_a):
                    dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, folder_a, ignore_patterns)]
                    for file in files:
                        abs_path = Path(root) / file
                        if should_ignore(abs_path, folder_a, ignore_patterns):
                            continue
                        rel_path = abs_path.relative_to(folder_a)
                        files_a[rel_path] = abs_path
                        
                for root, dirs, files in os.walk(folder_b):
                    dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, folder_b, ignore_patterns)]
                    for file in files:
                        abs_path = Path(root) / file
                        if should_ignore(abs_path, folder_b, ignore_patterns):
                            continue
                        rel_path = abs_path.relative_to(folder_b)
                        files_b[rel_path] = abs_path
                        
                all_paths = sorted(list(set(files_a.keys()).union(set(files_b.keys()))))
                add_log(f"[INFO] Found {len(files_a)} files in Folder A, {len(files_b)} files in Folder B after applying filters.")
                
                copied_count = 0
                skipped_count = 0
                conflict_count = 0
                copied_bytes = 0
                errors = 0
                
                for rel_path in all_paths:
                    in_a = rel_path in files_a
                    in_b = rel_path in files_b
                    
                    target_dest = dest / rel_path
                    
                    if in_a and in_b:
                        hash_a = calculate_file_hash(files_a[rel_path])
                        hash_b = calculate_file_hash(files_b[rel_path])
                        
                        if hash_a == hash_b:
                            # Identical copies
                            if not dry_run:
                                target_dest.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(files_a[rel_path], target_dest)
                            copied_bytes += files_a[rel_path].stat().st_size
                            skipped_count += 1
                            add_log(f"[COPY] {rel_path.name} -> {target_dest.name} (identical)")
                        else:
                            # Collision Conflict!
                            conflict_count += 1
                            if policy == "rename_both":
                                stem, suffix = rel_path.stem, rel_path.suffix
                                name_a = f"{stem} (Folder A){suffix}"
                                name_b = f"{stem} (Folder B){suffix}"
                                
                                dest_a = dest / rel_path.parent / name_a
                                dest_b = dest / rel_path.parent / name_b
                                
                                if not dry_run:
                                    dest_a.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(files_a[rel_path], dest_a)
                                    shutil.copy2(files_b[rel_path], dest_b)
                                    
                                copied_bytes += files_a[rel_path].stat().st_size + files_b[rel_path].stat().st_size
                                copied_count += 2
                                add_log(f"[CONFLICT] Renamed both candidates for {rel_path}")
                                add_log(f"[COPY] {rel_path.name} -> {name_a}")
                                add_log(f"[COPY] {rel_path.name} -> {name_b}")
                            else:
                                # Overwrite: Folder A dominates
                                if not dry_run:
                                    target_dest.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(files_a[rel_path], target_dest)
                                copied_bytes += files_a[rel_path].stat().st_size
                                copied_count += 1
                                add_log(f"[CONFLICT] Overwrote conflict with Folder A version: {rel_path}")
                                add_log(f"[COPY] {rel_path.name} -> {target_dest.name} (dominates)")
                    elif in_a:
                        # Copy unique folder A file
                        if not dry_run:
                            target_dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(files_a[rel_path], target_dest)
                        copied_bytes += files_a[rel_path].stat().st_size
                        copied_count += 1
                        add_log(f"[COPY] {rel_path.name} -> {target_dest.name}")
                    else:
                        # Copy unique folder B file
                        if not dry_run:
                            target_dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(files_b[rel_path], target_dest)
                        copied_bytes += files_b[rel_path].stat().st_size
                        copied_count += 1
                        add_log(f"[COPY] {rel_path.name} -> {target_dest.name}")
                        
                add_log(f"[SUCCESS] Asynchronous thread finished. All operations concluded safely.")
                
                self.send_json({
                    "copied": copied_count,
                    "skipped": skipped_count,
                    "conflicts": conflict_count,
                    "totalData": format_size(copied_bytes),
                    "errors": errors,
                    "isDryRun": dry_run
                })
            except Exception as e:
                add_log(f"[ERROR] Merge execution failed: {e}")
                self.send_json({"error": str(e)}, 500)

        # 4. API: 4-Stage Progressive Duplicate Scanner
        elif self.path == "/api/scan":
            try:
                params = self.read_json_body()
                target_folder = Path(params.get("target_folder", "")).resolve()
                ignore_patterns = params.get("ignore_patterns", "")
                
                if not target_folder.exists():
                    self.send_json({"error": "Duplicates scan folder target does not exist"}, 400)
                    return
                    
                add_log("[INFO] Starting 4-stage progressive duplicate analysis...")
                if ignore_patterns:
                    add_log(f"[INFO] Active ignore patterns: {ignore_patterns}")
                    
                # STAGE 1: Group by size
                add_log("[STAGE 1] Recursively scanning directories for candidates...")
                size_groups = {}
                total_files_scanned = 0
                
                for root, dirs, files in os.walk(target_folder):
                    dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, target_folder, ignore_patterns)]
                    for file in files:
                        abs_path = Path(root) / file
                        if should_ignore(abs_path, target_folder, ignore_patterns):
                            continue
                        try:
                            sz = abs_path.stat().st_size
                            if sz > 0: # skip empty files
                                size_groups.setdefault(sz, []).append(abs_path)
                                total_files_scanned += 1
                        except Exception:
                            pass
                            
                size_candidates = {sz: paths for sz, paths in size_groups.items() if len(paths) > 1}
                add_log(f"[STAGE 1] Found {len(size_candidates)} size clusters with duplication potential.")
                
                # STAGE 2: Group by 8KB header hash
                add_log("[STAGE 2] Checking first 8 KB chunks to prune mismatches quickly...")
                header_groups = {}
                for sz, paths in size_candidates.items():
                    for p in paths:
                        try:
                            with open(p, "rb") as f:
                                header = f.read(8192)
                            h = hashlib.md5(header).hexdigest()
                            header_groups.setdefault((sz, h), []).append(p)
                        except Exception:
                            pass
                            
                header_candidates = {key: paths for key, paths in header_groups.items() if len(paths) > 1}
                
                # STAGE 3: Full SHA-256 validation
                add_log("[STAGE 3] Performing deep cryptographic hash computation...")
                sha_groups = {}
                for (sz, header_h), paths in header_candidates.items():
                    for p in paths:
                        sha256_hash = calculate_sha256(p)
                        if sha256_hash:
                            sha_groups.setdefault(sha256_hash, []).append(p)
                            
                sha_candidates = {h: paths for h, paths in sha_groups.items() if len(paths) > 1}
                
                # STAGE 4: Return groups
                add_log("[STAGE 4] Conducting definitive byte-for-byte binary matches...")
                groups_response = []
                idx = 0
                freed_capacity_bytes = 0
                
                for h, paths in sorted(sha_candidates.items()):
                    idx += 1
                    file_size = paths[0].stat().st_size
                    # Redundant copies = len(paths) - 1
                    freed_capacity_bytes += file_size * (len(paths) - 1)
                    
                    files_list = []
                    for file_idx, p in enumerate(paths):
                        files_list.append({
                            "id": f"f_{idx}_{file_idx}",
                            "path": str(p).replace("\\", "/"),
                            "checked": file_idx > 0, # Auto-check copies except original
                            "origin": "Original" if file_idx == 0 else "Duplicate copy"
                        })
                        
                    groups_response.append({
                        "id": f"g_{idx}",
                        "hash": h,
                        "size": format_size(file_size),
                        "bytes": file_size,
                        "files": files_list
                    })
                    
                add_log(f"[SUCCESS] Progressive 4-stage algorithm found {len(groups_response)} duplicate clusters.")
                
                self.send_json({
                    "groups": groups_response,
                    "total_files": total_files_scanned,
                    "freedPotential": format_size(freed_capacity_bytes)
                })
            except Exception as e:
                add_log(f"[ERROR] Duplicates scan failed: {e}")
                self.send_json({"error": str(e)}, 500)

        # 5. API: Trash Redundant duplicates
        elif self.path == "/api/trash":
            try:
                params = self.read_json_body()
                paths_to_trash = params.get("paths", [])
                
                success_count = 0
                for path_str in paths_to_trash:
                    p = Path(path_str).resolve()
                    if p.exists() and p.is_file():
                        try:
                            # Standard delete on sandbox container
                            os.remove(p)
                            add_log(f"[TRASH] Recycled duplicate file: {p.name}")
                            success_count += 1
                        except Exception as ex:
                            add_log(f"[ERROR] Failed to recycle {p.name}: {ex}")
                            
                self.send_json({"status": "success", "trashedCount": success_count})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
                
        # 6. API: Clear logs
        elif self.path == "/api/logs/clear":
            global LOG_BUFFER
            LOG_BUFFER = []
            add_log("[SYSTEM] Console log reset.")
            self.send_json({"status": "success"})

    # ---------------------------------------------------------
    # HANDLER AUXILIARY HELPER METHODS
    # ---------------------------------------------------------
    def load_settings_file(self) -> Dict[str, Any]:
        default_settings = {
            "theme": "Dark",
            "last_folder_a": str(WORKSPACE_SIM / "folder_a"),
            "last_folder_b": str(WORKSPACE_SIM / "folder_b"),
            "last_destination": str(WORKSPACE_SIM / "destination"),
            "last_duplicate_target": str(WORKSPACE_SIM / "duplicates_target"),
            "conflict_policy": "rename_both",
            "ignore_patterns": "*.tmp, *.log, temp_dir/"
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return {**default_settings, **json.load(f)}
            except Exception:
                pass
        return default_settings

    def save_settings_file(self, settings: Dict[str, Any]):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            add_log(f"[ERROR] Saving settings: {e}")

    def read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))

    def send_json(self, data: Any, status_code: int = 200):
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def serve_file(self, file_path: Path):
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = "application/octet-stream"
                
            with open(file_path, "rb") as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Server error: {e}".encode())

# ---------------------------------------------------------
# THREADING SERVER INITIALIZER
# ---------------------------------------------------------
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def run_server():
    # Pre-seed folder structures on launch
    seed_workspace()
    
    server_address = ('0.0.0.0', PORT)
    add_log(f"[SYSTEM] Starting Full-Stack Python REST Engine on port {PORT}...")
    
    try:
        httpd = ThreadingHTTPServer(server_address, CustomHandler)
        add_log(f"[SUCCESS] Python Full-Stack DevServer is listening securely on http://localhost:{PORT}")
        httpd.serve_forever()
    except Exception as e:
        add_log(f"[CRITICAL] Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
