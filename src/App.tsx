/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from "react";
import { 
  Terminal as TerminalIcon, 
  GitBranch, 
  Cpu, 
  HelpCircle, 
  FolderTree, 
  Copy, 
  Check, 
  Code, 
  CheckCircle,
  ExternalLink,
  Laptop,
  CheckSquare
} from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState<"get_started" | "git_link" | "offline_faq" | "structure">("get_started");
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(id);
    setTimeout(() => setCopiedText(null), 2000);
  };

  return (
    <div className="h-full w-full flex flex-col font-sans bg-slate-950 text-slate-100 select-text selection:bg-blue-600/30">
      
      {/* HEADER */}
      <header className="px-6 py-4 flex items-center justify-between border-b border-slate-900 bg-slate-900/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-blue-400 rounded-lg flex items-center justify-center font-black text-white text-lg tracking-tight shadow-lg shadow-blue-500/10">
            FM
          </div>
          <div>
            <div className="text-base font-bold tracking-tight text-white leading-tight flex items-center gap-2">
              FileMorph Architect
              <span className="text-[10px] bg-blue-500/10 border border-blue-500/30 text-blue-400 font-mono px-1.5 py-0.5 rounded font-medium">
                Offline Core
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5 font-medium">
              Python Full-Stack Desktop Engine & Deployment Center
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] bg-slate-800 text-emerald-400 border border-slate-700/60 px-2.5 py-1 rounded-md font-mono font-semibold flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Desktop Ready
          </span>
        </div>
      </header>

      {/* NAVIGATION TABS */}
      <nav className="px-6 flex border-b border-slate-900 bg-slate-900/20">
        <button 
          onClick={() => setActiveTab("get_started")}
          className={`px-5 py-3.5 text-xs font-semibold tracking-wider uppercase border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === "get_started" 
              ? "border-blue-500 text-blue-400 bg-blue-500/5 font-bold" 
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Cpu className="w-4 h-4" /> 🚀 Local Setup
        </button>
        <button 
          onClick={() => setActiveTab("git_link")}
          className={`px-5 py-3.5 text-xs font-semibold tracking-wider uppercase border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === "git_link" 
              ? "border-blue-500 text-blue-400 bg-blue-500/5 font-bold" 
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <GitBranch className="w-4 h-4" /> 🐙 Link to Git
        </button>
        <button 
          onClick={() => setActiveTab("offline_faq")}
          className={`px-5 py-3.5 text-xs font-semibold tracking-wider uppercase border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === "offline_faq" 
              ? "border-blue-500 text-blue-400 bg-blue-500/5 font-bold" 
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <HelpCircle className="w-4 h-4" /> 📦 Offline Build & FAQ
        </button>
        <button 
          onClick={() => setActiveTab("structure")}
          className={`px-5 py-3.5 text-xs font-semibold tracking-wider uppercase border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === "structure" 
              ? "border-blue-500 text-blue-400 bg-blue-500/5 font-bold" 
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FolderTree className="w-4 h-4" /> 📂 Directory Map
        </button>
      </nav>

      {/* CORE DISPLAY PANELS */}
      <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full space-y-8">
        
        {/* TAB 1: LOCAL SETUP */}
        {activeTab === "get_started" && (
          <div className="space-y-6 animate-fade-in">
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Laptop className="w-5 h-5 text-blue-400" /> Run PySide6 Application Locally
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed mb-4">
                The full Python desktop application is safely stored in the <code className="text-emerald-400 font-mono">/desktop_app</code> directory.
                Follow these simple steps on your terminal to execute the application with high-performance native visual widgets.
              </p>

              {/* Step 1 */}
              <div className="mb-6">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-400 uppercase tracking-wider mb-2">
                  <span className="w-5 h-5 rounded-full bg-blue-500/10 flex items-center justify-center text-[10px] border border-blue-500/20">1</span>
                  Create Python Virtual Environment (Recommended)
                </div>
                <div className="relative">
                  <pre className="bg-slate-950 border border-slate-850 p-4 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto select-all">
                    {`# Navigate to project root, then set up virtual environment\npython -m venv .venv\n\n# Activate environment\n# On Windows:\n.venv\\Scripts\\activate\n# On macOS / Linux:\nsource .venv/bin/activate`}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(`python -m venv .venv`, "venv_setup")}
                    className="absolute top-3 right-3 text-slate-400 hover:text-white p-1.5 rounded bg-slate-900 border border-slate-800 transition-colors"
                    title="Copy command"
                  >
                    {copiedText === "venv_setup" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Step 2 */}
              <div className="mb-6">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-400 uppercase tracking-wider mb-2">
                  <span className="w-5 h-5 rounded-full bg-blue-500/10 flex items-center justify-center text-[10px] border border-blue-500/20">2</span>
                  Install PySide6 and Core Dependencies
                </div>
                <div className="relative">
                  <pre className="bg-slate-950 border border-slate-850 p-4 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto select-all">
                    {`pip install -r desktop_app/requirements.txt`}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(`pip install -r desktop_app/requirements.txt`, "pip_install")}
                    className="absolute top-3 right-3 text-slate-400 hover:text-white p-1.5 rounded bg-slate-900 border border-slate-800 transition-colors"
                  >
                    {copiedText === "pip_install" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Step 3 */}
              <div className="mb-2">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-400 uppercase tracking-wider mb-2">
                  <span className="w-5 h-5 rounded-full bg-blue-500/10 flex items-center justify-center text-[10px] border border-blue-500/20">3</span>
                  Launch Desktop Application
                </div>
                <div className="relative">
                  <pre className="bg-slate-950 border border-slate-850 p-4 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto select-all">
                    {`python desktop_app/main.py`}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(`python desktop_app/main.py`, "run_app")}
                    className="absolute top-3 right-3 text-slate-400 hover:text-white p-1.5 rounded bg-slate-900 border border-slate-800 transition-colors"
                  >
                    {copiedText === "run_app" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

            </div>

            <div className="border border-blue-500/10 bg-blue-500/5 rounded-xl p-5 flex items-start gap-3.5">
              <CheckCircle className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-slate-100 text-sm mb-1">Pre-built Binary Available via GitHub Actions</h4>
                <p className="text-slate-300 text-xs leading-relaxed">
                  Every time you push or sync your code to a GitHub repository, our configured GitHub Action compiles standalone executables for Windows, macOS, and Linux automatically. No compilation configurations needed on your machine!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: LINK TO GIT */}
        {activeTab === "git_link" && (
          <div className="space-y-6 animate-fade-in">
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-blue-400" /> Link This Codebase to GitHub/Git
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed mb-6">
                Connect your workspace directly to your GitHub account to commit files, track history, and release compiled desktop builds.
              </p>

              {/* Git Link Sequence */}
              <div className="space-y-4">
                
                {/* Step 1 */}
                <div className="bg-slate-950 border border-slate-900 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-300">STEP 1: Initialize Git Local Repository</span>
                    <button 
                      onClick={() => copyToClipboard(`git init\ngit add .\ngit commit -m "feat: init folder merger and duplicate scanner python core"`, "git_step1")}
                      className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 bg-slate-900 px-2.5 py-1 rounded border border-slate-800 transition-all cursor-pointer"
                    >
                      {copiedText === "git_step1" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Commands
                    </button>
                  </div>
                  <pre className="font-mono text-xs text-slate-400 leading-normal">
                    {`git init\ngit add .\ngit commit -m "feat: init folder merger and duplicate scanner python core"`}
                  </pre>
                </div>

                {/* Step 2 */}
                <div className="bg-slate-950 border border-slate-900 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-300">STEP 2: Connect Local Directory to GitHub Repository</span>
                    <button 
                      onClick={() => copyToClipboard(`git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git\ngit branch -M main`, "git_step2")}
                      className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 bg-slate-900 px-2.5 py-1 rounded border border-slate-800 transition-all cursor-pointer"
                    >
                      {copiedText === "git_step2" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Commands
                    </button>
                  </div>
                  <pre className="font-mono text-xs text-slate-400 leading-normal">
                    {`# Replace with your actual remote repository URL\ngit remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git\ngit branch -M main`}
                  </pre>
                </div>

                {/* Step 3 */}
                <div className="bg-slate-950 border border-slate-900 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-300">STEP 3: Push Source to GitHub Remote Branch</span>
                    <button 
                      onClick={() => copyToClipboard(`git push -u origin main`, "git_step3")}
                      className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 bg-slate-900 px-2.5 py-1 rounded border border-slate-800 transition-all cursor-pointer"
                    >
                      {copiedText === "git_step3" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Command
                    </button>
                  </div>
                  <pre className="font-mono text-xs text-slate-400 leading-normal">
                    {`git push -u origin main`}
                  </pre>
                </div>

              </div>
            </div>

            {/* Git ignore reminder */}
            <div className="bg-slate-900/20 border border-slate-850 rounded-xl p-5">
              <h4 className="font-semibold text-xs text-slate-300 mb-1 flex items-center gap-1.5">
                <CheckSquare className="w-4 h-4 text-emerald-400" /> Optimized .gitignore Ready
              </h4>
              <p className="text-slate-400 text-xs leading-relaxed">
                We have already written an optimized <code className="text-blue-400">.gitignore</code> in the workspace root. It safely excludes local caches, virtual environments (<code className="text-slate-400">.venv/</code>), execution logs, and compiled binaries, keeping your Git repository pristine.
              </p>
            </div>
          </div>
        )}

        {/* TAB 3: OFFLINE FAQ & STANDALONE BUILDS */}
        {activeTab === "offline_faq" && (
          <div className="space-y-6 animate-fade-in">
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 space-y-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Code className="w-5 h-5 text-blue-400" /> Standalone Executable & Offline Capabilities FAQ
              </h2>

              {/* Q1 */}
              <div className="border-b border-slate-800/80 pb-5">
                <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  Will the compiled executable work offline without any dependencies?
                </h3>
                <p className="text-slate-300 text-xs leading-relaxed pl-3.5">
                  <strong>Yes, 100% offline.</strong> Once PyInstaller builds the package, it extracts and bundles the Python interpreter, visual Qt framework (PySide6), file algorithms, styling, and standard libraries into a <strong>single standalone binary file</strong> (e.g. <code className="text-blue-400">MergerDuplicateFinder.exe</code> on Windows or native executable on macOS/Linux). 
                  The target machine <strong>does not need</strong> Python installed, nor does it require any internet connectivity.
                </p>
              </div>

              {/* Q2 */}
              <div className="border-b border-slate-800/80 pb-5">
                <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  What packaging method is configured?
                </h3>
                <p className="text-slate-300 text-xs leading-relaxed pl-3.5">
                  We use PyInstaller with the <code className="text-slate-400">--onefile</code> and <code className="text-slate-400">--windowed</code> configurations. 
                  This compresses all internal assets and modules into one self-contained executable. When run, it extracts its temporary libraries into system cache memory, displays the Sleek graphical interface immediately, and closes clean.
                </p>
              </div>

              {/* Q3 */}
              <div>
                <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  How to compile the executable manually?
                </h3>
                <p className="text-slate-300 text-xs leading-relaxed pl-3.5 mb-3">
                  If you want to package the app manually on your computer rather than relying on GitHub Actions:
                </p>
                <div className="relative">
                  <pre className="bg-slate-950 border border-slate-850 p-4 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto select-all">
                    {`# Install packaging toolkit\npip install pyinstaller\n\n# Compile main script into a single windowed executable\npyinstaller --onefile --windowed --name="MergerDuplicateFinder" desktop_app/main.py`}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(`pip install pyinstaller\npyinstaller --onefile --windowed --name="MergerDuplicateFinder" desktop_app/main.py`, "manual_compile")}
                    className="absolute top-3 right-3 text-slate-400 hover:text-white p-1.5 rounded bg-slate-900 border border-slate-800 transition-colors"
                  >
                    {copiedText === "manual_compile" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 4: DIRECTORY STRUCTURE */}
        {activeTab === "structure" && (
          <div className="space-y-6 animate-fade-in">
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <FolderTree className="w-5 h-5 text-blue-400" /> Workspace Directory Structure
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed mb-6">
                Your workspace is organized according to the clean modular guidelines originally outlined, isolating the desktop application code from local build configurations.
              </p>

              <div className="bg-slate-950 border border-slate-900 rounded-lg p-5 font-mono text-xs leading-relaxed text-slate-300 select-text">
                <div className="text-slate-500"># Current Project Layout</div>
                <div className="mt-2">📁 filemorph-workspace/</div>
                <div className="pl-4 text-slate-400">├── 📁 .github/</div>
                <div className="pl-8 text-slate-500">└── 📁 workflows/</div>
                <div className="pl-12 text-emerald-400">└── 📄 build-binaries.yml <span className="text-slate-600"># Free-Tier CI/CD build actions</span></div>
                <div className="pl-4 text-emerald-400">├── 📁 desktop_app/</div>
                <div className="pl-8 text-blue-400">├── 📄 main.py <span className="text-slate-600"># Core desktop visual script (PySide6)</span></div>
                <div className="pl-8 text-blue-400">└── 📄 requirements.txt <span className="text-slate-600"># Python pip packages</span></div>
                <div className="pl-4 text-slate-400">├── 📄 AGENTS.md <span className="text-slate-600"># Codebase instructions & algorithms map</span></div>
                <div className="pl-4 text-slate-400">├── 📄 metadata.json <span className="text-slate-600"># App metadata config</span></div>
                <div className="pl-4 text-slate-400">└── 📄 .gitignore <span className="text-slate-600"># Git clean exclusions</span></div>
              </div>
            </div>
          </div>
        )}

      </div>
      
    </div>
  );
}
