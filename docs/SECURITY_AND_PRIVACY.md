# Security and privacy

Do not commit or publish:

- `config.json`
- log files
- SoundCork `data/`
- `Sources.xml`
- `DeviceInfo.xml`
- `Presets.xml`
- `Recents.xml`
- `OverrideSdkPrivateCfg.xml`
- speaker serial numbers
- account IDs
- private LAN topology

`Sources.xml` can contain source secrets/tokens and should be treated as private.

This editor only needs local LAN access to:

- Bose speaker HTTP API on port 8090
- SoundCork HTTP server, usually port 8000

No cloud credentials are needed by this editor.
