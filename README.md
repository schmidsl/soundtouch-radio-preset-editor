# SoundTouch Radio Preset Editor for SoundCork

A small local GUI tool for Bose SoundTouch speakers that are already configured to use [SoundCork](https://github.com/deborahgu/soundcork).

It is built for one narrow job:

> Search TuneIn stations through your local SoundCork server, preview them, and store them on Bose SoundTouch hardware preset buttons 1–6.

This tool is **not** a SoundCork installer. It does **not** switch your speaker to SoundCork. It assumes you already have a working SoundCork setup.

## Features

- Show the six current hardware presets.
- Play existing presets from the GUI.
- Check whether SoundCork is reachable.
- Search TuneIn through SoundCork's local BMX/TuneIn endpoint.
- Show only real station results; shows/podcasts are ignored.
- Preview a station before saving it.
- Save the selected station to hardware preset slot 1–6.
- Automatically create a ZIP backup before each preset change.
- Update SoundCork's `Presets.xml` copy after saving.
- Restart the SoundCork Docker service after saving, if configured.

## Requirements

- Windows 10/11.
- Python 3.12 with Tkinter.
- A Bose SoundTouch speaker reachable on the local network.
- SoundCork already running locally.
- The speaker already configured to use SoundCork.
- Docker installed only if you want the editor to restart SoundCork automatically.

No external Python packages are required.

## Quick start

1. Download the release ZIP and extract it, for example to:

   ```text
   F:\soundcork\RADIO_PRESET_EDITOR
   ```

2. Copy:

   ```text
   config.example.json
   ```

   to:

   ```text
   config.json
   ```

3. Edit `config.json`:

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

   `account_id` is optional. If left empty, the editor tries to find the first `data/*/Presets.xml` inside the SoundCork directory.

4. Start the editor by double-clicking:

   ```text
   START_EDITOR.bat
   ```

## How it works

The editor uses local HTTP endpoints:

- Read presets:

  ```text
  GET http://<bose-ip>:8090/presets
  ```

- Play an existing preset or search result:

  ```text
  POST http://<bose-ip>:8090/select
  ```

- Search TuneIn via SoundCork:

  ```text
  GET http://<soundcork-base>/bmx/tunein/v1/search?q=...
  ```

- Save a station to a hardware preset slot:

  ```text
  POST http://<bose-ip>:8090/storePreset
  ```

## Safety model

Before every preset change, the editor creates a ZIP backup of the configured `soundcork_dir` into `backup_dir`.

The editor does **not** restore backups. It does not overwrite the whole SoundCork folder. It only writes a selected station to a selected preset slot by using the speaker's local `/storePreset` endpoint.

## Important privacy note

Do not publish your local `config.json`, logs, `Sources.xml`, `DeviceInfo.xml`, or SoundCork data directory. They may contain device IDs, account IDs, serial numbers, source secrets, or private network details.

## Known limitations

- Only TuneIn station results are supported in v0.4.0.
- Shows, podcasts and tracklists are intentionally filtered out.
- Spotify, Deezer, Amazon, SiriusXM, DLNA and direct stream editing are not supported.
- This tool assumes SoundCork is already working.
- The UI is intentionally simple and local-first.

## German Kurzfassung

Dieses Tool ist ein kleiner lokaler Preset-Editor für Bose SoundTouch + SoundCork. Es zeigt sechs Presets, sucht TuneIn-Sender über SoundCork, spielt Suchergebnisse probeweise ab und speichert Sender auf Hardwaretaste 1–6. Vor jeder Änderung wird automatisch ein Backup erstellt.

Start im Alltag:

```text
START_EDITOR.bat
```

## License

MIT License. See `LICENSE`.
