# Troubleshooting

## The editor says config.json is missing

Copy `config.example.json` to `config.json` and edit the IPs and paths.

## Presets cannot be loaded

Check whether the Bose speaker is reachable:

```powershell
Invoke-WebRequest -UseBasicParsing "http://<bose-ip>:8090/info"
Invoke-WebRequest -UseBasicParsing "http://<bose-ip>:8090/presets"
```

## SoundCork search fails

Check whether SoundCork is reachable:

```powershell
Invoke-WebRequest -UseBasicParsing "http://<soundcork-ip>:8000/admin"
Invoke-WebRequest -UseBasicParsing "http://<soundcork-ip>:8000/bmx/tunein/v1/search?q=radio+b138"
```

The correct search route is:

```text
/bmx/tunein/v1/search?q=...
```

not:

```text
/v1/search?q=...
```

## Preview works but saving fails

Check:

- Bose IP is correct.
- `/storePreset` is reachable.
- The selected result is a station, not a show/podcast.
- SoundCork is running.

## Save works but SoundCork restart fails

Set this in `config.json`:

```json
"restart_soundcork_after_save": false
```

Then restart SoundCork manually.

## Docker is slow after Windows reboot

On some small Windows PCs, Docker Desktop can take several minutes to become ready after login. Wait a few minutes before using preset buttons immediately after reboot.
