# Welcome to MVC Calculator

MVC Calculator calculates the Maximum Voluntary Contraction based on the signal processing guidelines in [@Konrad05].

## Why don't we just use a script for this calculation?  
sEMG can be a bit noisy.  Depending in the testing protocol and the success of the recording session, thia noise can make it's weay into the measurement process.  By allowing ther user to define the MVC bursts, MVC caluclator provides a **visual** method of reducing noise.  MVC Calculator also provides a method for saving, loading, and modifying MVC.  

## Quick start
The input files to MVC Calculator are .mat files creasted by Qualisys.  The system uses this data structure to extract data from all sensors.

!!! remember "Remember"
    Noraxon/Qualisys doesn't know or care, which sensors are the target for the MVC.  All sesnor data will record all sensors regardless.  It is up to the user to not only identify the relevant sensor from all those 
	

## Measurement protocol suggestions
The system is written to follow the 'best of 3' procedure in [@Konrad05].


!!! note "Note"
	To change the 'best of x' x = no of selections, change the BEST_OF variable in ./config/defaults.py


## TODOs in MkDocs


- Test 4 in tests/test_plot_controller.py::test_row_click_bolds_correct_row FAILED  
- FINISH a splash screen
- Proper citations from bibtex
- Create a template for future Spyder GUI projects
- WiX to create .msi installer file a la Blender
- Track called methods - look for redundant code etc, etc, etc
- Vulture for dead code finding




🧭 Overview

Creating an .msi installer involves two main stages:

Packaging your app into a standalone executable (using PyInstaller or similar).

Wrapping that executable into a Windows installer (using MSI tools like msitools, WiX, or NSIS).

We’ll focus on the modern approach:
👉 PyInstaller + WiX Toolset, since it produces professional, signed .msi installers used by Blender, OBS, and others.

🧱 Step 1 — Prepare Your PyQt5 App

Make sure your app runs fine as:

python main.py


If it uses relative paths (for icons, UI files, etc.), make sure you handle both development and frozen modes:

import sys, os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

⚙️ Step 2 — Create a PyInstaller .spec File

Install PyInstaller:

pip install pyinstaller


Generate a base .spec:

pyinstaller --name "MVC_Calculator" --noconfirm --windowed main.py


Then edit the .spec file to include:

Icons (icon='app.ico')

Additional data (UI files, logos, docs)

Hidden imports (for PyQt5)

Example snippet:

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('ui/*.ui', 'ui'), ('img/*', 'img'), ('docs_site/site', 'help')],
    hiddenimports=['PyQt5.sip', 'PyQt5.QtPrintSupport'],
    noarchive=False,
)


Then rebuild:

pyinstaller MVC_Calculator.spec


Output folder:

dist/MVC_Calculator/
    ├── MVC_Calculator.exe
    ├── Qt5Core.dll
    ├── platforms/
    └── ...


✅ At this point, your app is a standalone EXE.

📦 Step 3 — Install the WiX Toolset

Download and install WiX 3.11 or later:
👉 https://wixtoolset.org/releases/

Add WiX to your PATH:

set PATH=%PATH%;C:\Program Files (x86)\WiX Toolset v3.11\bin


WiX gives you tools like:

candle.exe — compiles WiX source files (.wxs)

light.exe — links compiled object files into an .msi

🧰 Step 4 — Create a .wxs Installer Definition

Create a file called installer.wxs:

<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="MVC Calculator" Language="1033" Version="1.0.0" Manufacturer="Moviolabs" UpgradeCode="PUT-GUID-HERE">
    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine" />
    <MajorUpgrade AllowDowngrades="no" />
    <MediaTemplate />

    <Feature Id="MainFeature" Title="MVC Calculator" Level="1">
      <ComponentGroupRef Id="AppFiles" />
    </Feature>

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="MVC Calculator" />
      </Directory>
    </Directory>

    <ComponentGroup Id="AppFiles" Directory="INSTALLFOLDER">
      <Component Id="MainExe" Guid="PUT-NEW-GUID-HERE">
        <File Source="dist\MVC_Calculator\MVC_Calculator.exe" />
      </Component>
    </ComponentGroup>

    <Icon Id="appicon.ico" SourceFile="app.ico"/>
    <Property Id="ARPPRODUCTICON" Value="appicon.ico"/>
  </Product>
</Wix>


Use PowerShell to generate new GUIDs:

[guid]::NewGuid()

🧩 Step 5 — Compile the Installer

Run WiX tools from your project folder:

candle installer.wxs
light installer.wixobj -o MVC_Calculator.msi


✅ You now have:

MVC_Calculator.msi


This .msi:

Installs to C:\Program Files\MVC Calculator

Adds uninstall entry in Control Panel

Supports repair/uninstall

Looks and behaves like Blender’s installer

🔐 Step 6 — (Optional) Code Sign Your MSI

To prevent Windows SmartScreen warnings, sign the MSI using a valid certificate:

signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 MVC_Calculator.msi

🧹 Step 7 — Optional Extras

Create shortcuts
Add <Shortcut> elements in your .wxs inside the Component.

Include registry keys
To add uninstall info or defaults, use <RegistryValue>.

Bundle dependencies
Use datas=[...] in .spec for PyQt5 platforms, icons, docs, etc.

Versioning
Use a dynamic version from your __version__ or VERSION.txt file.

⚡ Alternative: Automatic MSI Creation with cx_Freeze or fbs

If you prefer simplicity over full control:

🧊 Using fbs (built on PyInstaller)
pip install fbs
fbs startproject
fbs run
fbs freeze
fbs installer


This produces an .msi automatically — perfect for PyQt5.

🧭 Recommended Workflow Summary
Stage	Tool	Purpose
Package app	PyInstaller	Bundle into single-folder EXE
Build installer	WiX	Professional MSI
Sign installer	signtool	Remove SmartScreen warnings

If you’d like, I can generate a ready-to-use example (.spec, .wxs, and build script) tailored for your current PyQt5 app — just tell me:

The main file (e.g. main.py)

App name and version

Icon path
and I’ll produce a fully working setup.

Would you like me to do that?


🧭 1. Find which classes/functions are actually used from main.py
🔹 Static analysis tools
These inspect the structure of your code without running it.


pyan3 – builds a call graph showing which functions/classes call which others.
pip install pyan3
pyan3 main.py yourpackage/**/*.py --dot > callgraph.dot

Then visualize:
dot -Tpng callgraph.dot -o callgraph.png

This will show which classes/functions are actually referenced from main.py.


pycg (Python Call Graph) – more advanced, builds inter-module call graphs:
pip install pycg
pycg --package yourpackage --entry-file main.py --output callgraph.json

You can inspect callgraph.json to see what’s reachable from main.py.



⚙️ 2. Find which code is actually executed
🔹 Dynamic runtime tracing
Run your app and track what gets called.


coverage.py (most popular)
pip install coverage
coverage run main.py
coverage html

Then open htmlcov/index.html.


Any file or line not executed = dead / unused code.


Great for spotting redundant methods and unreachable classes.




pycallgraph2 – generates runtime call graphs:
pip install pycallgraph2
python -m pycallgraph --output-file=graph.png yourscript.py

You’ll get a flow diagram of all called functions.


trace module (built-in)
python -m trace --trace main.py

Prints every function call as it happens (no install required).



🧹 3. Detect redundant / unreachable / duplicated code
🔹 Dead code finders


vulture – best tool for unused functions, variables, and classes.
pip install vulture
vulture yourproject/

Output example:
yourmodule.py:42: unused function 'old_calibrate'
yourdialog.py:88: unused class 'LegacyDialog'

Combine it with coverage.py for accuracy (static + dynamic).


🔹 Duplication checkers


flake8 + plugins:


flake8-unused-arguments


flake8-dead-code


flake8-eradicate (finds commented-out code)




jscpd (language-agnostic):
npx jscpd --languages python --reporters console --min-tokens 50 .

Detects copied/pasted code segments.



🧠 4. Recommended workflow
GoalBest ToolsFind unused classes/functionsvultureVisualize function/class call relationshipspyan3, pycgVerify which code runscoverage.py, traceFind duplicate codejscpd, flake8-eradicateAudit imports / unused variablesflake8, pylint, ruff

If you want, I can help you:


🔍 Run these tools step-by-step on your MOTUS or MVC Calculator repository,


🧩 Produce a dependency graph showing which classes are actually called from main.py,


🧼 Generate a “redundancy report” combining vulture + coverage.


Would you like me to outline that exact combined workflow (e.g., commands + report integration)?

<!-- 
## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.




## Bibliography
::: bibliography

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
 -->