# API notes

This editor uses local endpoints observed in Bose SoundTouch / SoundCork setups.

## Bose speaker

Read current presets:

```text
GET http://<bose-ip>:8090/presets
```

Play a content item:

```text
POST http://<bose-ip>:8090/select
```

Store a preset:

```text
POST http://<bose-ip>:8090/storePreset
```

Example store body:

```xml
<preset id="6">
  <ContentItem source="TUNEIN" type="stationurl" location="/v1/playback/station/s114357" sourceAccount="" isPresetable="true">
    <itemName>Radio B138</itemName>
    <containerArt>http://cdn-profiles.tunein.com/s114357/images/logoq.png</containerArt>
  </ContentItem>
</preset>
```

## SoundCork

Search TuneIn stations:

```text
GET http://<soundcork-base>/bmx/tunein/v1/search?q=<query>
```

The editor uses the `bmx_sections` section named `Stations` and the `_links.bmx_preset` object to build Bose `ContentItem` XML.
