# Setup

## 1. Install Python 3.12

On Windows, install Python 3.12. Tkinter is included with the standard Python installer.

Check:

```powershell
py -3.12 --version
py -3.12 -c "import tkinter as tk; print('TK_OK', tk.TkVersion)"
```

## 2. Extract this release

Example:

```text
F:\soundcork\RADIO_PRESET_EDITOR
```

The editor does not need to live inside the SoundCork folder, but it is convenient.

## 3. Create config.json

Copy:

```text
config.example.json
```

to:

```text
config.json
```

Edit the values:

```json
{
  "bose_ip": "192.168.1.50",
  "soundcork_base": "http://192.168.1.10:8000",
  "soundcork_dir": "F:/soundcork",
  "backup_dir": "F:/Backups/soundcork",
  "account_id": "",
  "restart_soundcork_after_save": true,
  "docker_compose_file": "",
  "docker_service_name": "soundcork",
  "request_timeout_seconds": 12
}
```

## 4. Start

Double-click:

```text
START_EDITOR.bat
```

or from PowerShell:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\START_EDITOR.ps1
```

## 5. First checks

Inside the editor:

1. Click **Presets neu laden**.
2. Click **SoundCork Status prüfen**.
3. Click **ABSPIELEN** on an existing preset.
4. Search for a station.
5. Preview the search result.
6. Save only after preview works.
