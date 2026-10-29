"""Build a single-file executable in dist/: python scripts/build_exe.py (needs pip install pyinstaller)."""

from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parents[1]

PyInstaller.__main__.run([
    str(ROOT / "scripts" / "run_theblackhole.py"),
    "--name", "TheBlackHole",
    "--onefile",
    "--windowed",  # No console window
    "--paths", str(ROOT / "src"),
    "--distpath", str(ROOT / "dist"),
    "--workpath", str(ROOT / "build"),
    "--specpath", str(ROOT / "build"),
    "--noconfirm",
])
