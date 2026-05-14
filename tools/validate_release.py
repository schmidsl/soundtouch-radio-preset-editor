from pathlib import Path
import json
import py_compile

ROOT = Path(__file__).resolve().parent.parent

required = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "RELEASE_NOTES_v0.4.0.md",
    "config.example.json",
    "START_EDITOR.bat",
    "START_EDITOR.ps1",
    "src/soundtouch_radio_preset_editor.py",
    "docs/SETUP.md",
    "docs/TROUBLESHOOTING.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/API_NOTES.md",
]

missing = [p for p in required if not (ROOT / p).exists()]
if missing:
    raise SystemExit(f"Missing files: {missing}")

with (ROOT / "config.example.json").open("r", encoding="utf-8") as f:
    json.load(f)

py_compile.compile(str(ROOT / "src/soundtouch_radio_preset_editor.py"), doraise=True)

print("Release validation passed.")
