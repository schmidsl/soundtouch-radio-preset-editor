# SoundTouch Radio Preset Editor 🎛️📻

A small local TuneIn radio preset editor for **Bose SoundTouch** speakers running with **SoundCork**.

This tool lets you search TuneIn stations through your local SoundCork server, preview them, and save them directly to the six hardware preset buttons of a Bose SoundTouch speaker.

It was built for one simple purpose:

> Keep old SoundTouch hardware useful after cloud-dependent services become unreliable or disappear.

---

## ✨ Features

- 📻 Show the six current Bose SoundTouch hardware presets
- ▶️ Play existing presets directly from the editor
- 🔎 Search TuneIn through the local SoundCork BMX/TuneIn endpoint
- 🎧 Preview stations before saving them
- 💾 Save selected stations to hardware preset slots 1–6
- 🧯 Create an automatic ZIP backup before every preset change
- 🔁 Sync SoundCork’s local `Presets.xml` after saving
- 🐳 Restart the SoundCork container after preset updates
- 🪟 Simple local desktop UI using Python + Tkinter
- 🧰 No cloud account required by this tool itself

---

## 🧠 What this tool is

This is a **local preset editor** for an already working SoundCork setup.

It talks to:

```text
Bose SoundTouch speaker  →  local SoundTouch API
SoundCork server         →  local TuneIn/BMX search API

The editor uses these local endpoints:

GET  http://<BOSE_IP>:8090/presets
POST http://<BOSE_IP>:8090/select
POST http://<BOSE_IP>:8090/storePreset

GET  http://<SOUNDCORK_HOST>:8000/bmx/tunein/v1/search?q=...
🚫 What this tool is not

This tool does not:

install SoundCork
switch your speaker from Bose cloud services to SoundCork
configure OverrideSdkPrivateCfg.xml
enable SSH or remote_services
manage Spotify, Deezer, Amazon Music, SiriusXM, or other account-based services
restore full SoundCork backups
modify your speaker firmware

It assumes:

SoundCork is already installed.
Your Bose speaker is already configured to use SoundCork.
The speaker and SoundCork server are reachable on your local network.
✅ Tested use case

This editor is designed around this workflow:

1. Open the editor
2. Search for a TuneIn radio station
3. Preview the station
4. Choose preset slot 1–6
5. Save
6. Press the physical Bose preset button
7. Radio plays

Perfect for:

internet radio
local-first Bose SoundTouch usage
replacing old TuneIn preset management
avoiding cloud-dependent preset editing
keeping old SoundTouch hardware useful
📦 Requirements
Windows
Windows 10 or later
Python 3.12
SoundCork running locally
Bose SoundTouch speaker reachable on the network
Docker only required if your SoundCork installation runs in Docker
Python

The editor uses only Python standard library modules:

tkinter
urllib
json
xml
subprocess
pathlib
datetime

No external Python packages are required.

🚀 Quick start
1. Download or clone this repository
git clone https://github.com/YOUR_USERNAME/soundtouch-radio-preset-editor.git
cd soundtouch-radio-preset-editor

Or download the release ZIP and extract it.

2. Create your local config

Copy:

config.example.json

to:

config.json

Edit config.json for your local setup:

{
  "bose_ip": "192.168.0.119",
  "soundcork_base": "http://192.168.0.10:8000",
  "soundcork_dir": "F:/soundcork",
  "backup_dir": "F:/Backups/soundcork",
  "account_id": "9442110",
  "docker_compose_file": "F:/soundcork/docker-compose.yml",
  "soundcork_service_name": "soundcork"
}

Example meaning:

bose_ip               IP address of your Bose SoundTouch speaker
soundcork_base        Base URL of your local SoundCork server
soundcork_dir         Local SoundCork directory
backup_dir            Directory where automatic backups are stored
account_id            SoundCork/Bose account folder ID
docker_compose_file   Path to your SoundCork docker-compose.yml
soundcork_service_name Docker Compose service name
▶️ Run the editor
Recommended on Windows

Double-click:

START_EDITOR.bat

Or run:

.\START_EDITOR.ps1

Manual Python start:

py -3.12 src\soundtouch_radio_preset_editor.py
🖥️ How to use
Show current presets

When the editor starts, it reads the current presets from:

http://<BOSE_IP>:8090/presets

You will see six preset cards.

Each card shows:

Preset number
Station name
Source
Location
ABSPIELEN / Play button
Play an existing preset ▶️

Click:

ABSPIELEN

The editor sends the preset’s ContentItem to:

POST http://<BOSE_IP>:8090/select

This plays the station without changing the preset.

Search TuneIn 🔎

Use the search field on the right.

Example searches:

radio b138
radio wien
orf radio oberoesterreich
fm4
life radio

The editor searches through SoundCork:

GET http://<SOUNDCORK_HOST>:8000/bmx/tunein/v1/search?q=...

Only real TuneIn station results are shown.

Shows, podcasts, and tracklists are ignored.

Preview a station 🎧

Select a search result and click:

SUCHERGEBNIS PROBE ABSPIELEN

The selected station will play immediately, but no preset is changed.

This is useful before overwriting a hardware button.

Save station to preset slot 💾
Search for a station
Select the result
Preview it
Choose slot 1 to 6
Click:
AUSWAHL AUF SLOT SPEICHERN

Before writing anything, the editor creates a ZIP backup.

Then it sends:

POST http://<BOSE_IP>:8090/storePreset

After saving, it:

1. reads the fresh /presets from the speaker
2. updates SoundCork's local Presets.xml
3. restarts the SoundCork container
4. reloads the UI
🧯 Backups

Before every preset change, the editor creates a backup ZIP in:

backup_dir

Example:

F:/Backups/soundcork/soundcork_BACKUP_BEFORE_PRESET_CHANGE_20260515_001531.zip

Backups are intentionally stored outside the live SoundCork directory.

Recommended layout:

F:/soundcork              live SoundCork system
F:/Backups/soundcork      backups
🔐 Privacy and safety

This repository should not contain:

real device IDs
real account IDs
real serial numbers
real Sources.xml
real DeviceInfo.xml
real Presets.xml
real logs
real backups
real local config.json

The included .gitignore excludes local/private files.

Never publish:

config.json
Sources.xml
DeviceInfo.xml
OverrideSdkPrivateCfg.xml
backup ZIPs
logs
⚠️ Important limitations

This editor currently focuses on:

TUNEIN stationurl presets

It does not manage:

Spotify
Deezer
Amazon Music
SiriusXM
Pandora
DLNA
Bluetooth
AUX
custom stream proxies

The editor may find more TuneIn stations than the old Bose app, because it uses the local SoundCork TuneIn/BMX search endpoint directly.

🧩 How it works

A TuneIn search result contains data like:

{
  "name": "Radio B138",
  "href": "/v1/playback/station/s114357",
  "type": "stationurl",
  "containerArt": "http://cdn-profiles.tunein.com/s114357/images/logoq.png"
}

The editor converts this into a Bose ContentItem:

<ContentItem source="TUNEIN" type="stationurl" location="/v1/playback/station/s114357" sourceAccount="" isPresetable="true">
  <itemName>Radio B138</itemName>
  <containerArt>http://cdn-profiles.tunein.com/s114357/images/logoq.png</containerArt>
</ContentItem>

To save it to preset slot 6, the editor sends:

<preset id="6">
  <ContentItem source="TUNEIN" type="stationurl" location="/v1/playback/station/s114357" sourceAccount="" isPresetable="true">
    <itemName>Radio B138</itemName>
    <containerArt>http://cdn-profiles.tunein.com/s114357/images/logoq.png</containerArt>
  </ContentItem>
</preset>

to:

POST http://<BOSE_IP>:8090/storePreset
🛠️ Troubleshooting
Editor starts, but no presets appear

Check that the Bose speaker is reachable:

Invoke-WebRequest -UseBasicParsing "http://<BOSE_IP>:8090/presets"
TuneIn search fails

Check that SoundCork is reachable:

Invoke-WebRequest -UseBasicParsing "http://<SOUNDCORK_HOST>:8000/admin"

Then test search manually:

Invoke-WebRequest -UseBasicParsing "http://<SOUNDCORK_HOST>:8000/bmx/tunein/v1/search?q=radio+b138"
Saving works, but SoundCork does not update

Check your config:

"soundcork_dir": "F:/soundcork",
"account_id": "9442110",
"docker_compose_file": "F:/soundcork/docker-compose.yml",
"soundcork_service_name": "soundcork"

The editor must be able to update:

<soundcork_dir>/data/<account_id>/Presets.xml
Docker restart fails

Check Docker:

docker info
docker compose -f "F:/soundcork/docker-compose.yml" ps

Restart manually:

docker compose -f "F:/soundcork/docker-compose.yml" restart soundcork
Speaker does not play after PC reboot

SoundCork may need a few minutes to start after Windows login.

Recommended:

Wait 4–5 minutes after reboot before pressing preset buttons.
🗂️ Suggested folder layout
F:/
├── soundcork/
│   ├── docker-compose.yml
│   ├── data/
│   └── RADIO_PRESET_EDITOR/
│
└── Backups/
    └── soundcork/
🧪 Development status

Current release:

v0.4.0

Implemented:

✅ read presets
✅ play presets
✅ search TuneIn
✅ preview TuneIn stations
✅ save TuneIn stations to slots 1–6
✅ automatic backup before changes
✅ SoundCork Presets.xml sync
✅ SoundCork container restart

Not implemented:

❌ restore from backup
❌ Spotify preset management
❌ Deezer preset management
❌ multi-speaker UI
❌ non-TuneIn custom stream editor
🧭 Design principle

This tool intentionally stays small.

It does one thing:

Manage TuneIn radio presets for a SoundCork-backed Bose SoundTouch speaker.

No cloud.
No account management.
No large platform.
No unnecessary abstraction.

Just:

Search → Preview → Save → Press hardware button → Radio plays
📜 License

This project is released under The Unlicense.

See:

LICENSE
🙏 Credits

Built around the local SoundTouch API and SoundCork’s local TuneIn/BMX endpoints.

This project is not affiliated with Bose, SoundCork, TuneIn, or any related service provider.

Bose and SoundTouch are trademarks of their respective owners.

💡 Why this exists

Old hardware should not become useless just because a cloud service changes.

This project is a small local-first tool to keep a useful radio device useful.

📻✨
