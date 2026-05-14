"""
SoundTouch Radio Preset Editor for SoundCork
Version: 0.4.0

A small local GUI tool for Bose SoundTouch speakers that are already
configured to use SoundCork. It can read six presets, play/preview stations,
search TuneIn through the local SoundCork BMX endpoint, and store a selected
station to hardware preset slot 1-6.

This tool intentionally does not install SoundCork and does not switch a
speaker to SoundCork. It assumes that SoundCork is already running.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tkinter as tk
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from tkinter import messagebox, ttk

APP_NAME = "SoundTouch Radio Preset Editor"
APP_VERSION = "0.4.0"

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "config.json"
CONFIG_EXAMPLE_PATH = APP_DIR / "config.example.json"
LOG_FILE = APP_DIR / "radio_preset_editor.log"
PROOF_DIR = APP_DIR / "proof"


@dataclass
class AppConfig:
    bose_ip: str
    soundcork_base: str
    soundcork_dir: Path
    backup_dir: Path
    account_id: str = ""
    restart_soundcork_after_save: bool = True
    docker_compose_file: str = ""
    docker_service_name: str = "soundcork"
    request_timeout_seconds: int = 12

    @property
    def bose_base(self) -> str:
        return f"http://{self.bose_ip}:8090"

    @property
    def soundcork_admin(self) -> str:
        return f"{self.soundcork_base.rstrip('/')}/admin"

    @property
    def soundcork_search(self) -> str:
        return f"{self.soundcork_base.rstrip('/')}/bmx/tunein/v1/search"

    @property
    def compose_file(self) -> Path:
        if self.docker_compose_file:
            return Path(self.docker_compose_file)
        return self.soundcork_dir / "docker-compose.yml"


def log(message: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{stamp}  {message}\n")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        if CONFIG_EXAMPLE_PATH.exists():
            shutil.copy2(CONFIG_EXAMPLE_PATH, CONFIG_PATH)
            msg = (
                "config.json wurde aus config.example.json erstellt.\n\n"
                "Bitte config.json öffnen, Bose-IP, SoundCork-URL, SoundCork-Ordner "
                "und Backup-Ordner prüfen und den Editor danach erneut starten."
            )
            raise RuntimeError(msg)
        raise RuntimeError("config.json fehlt und config.example.json wurde nicht gefunden.")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    required = ["bose_ip", "soundcork_base", "soundcork_dir", "backup_dir"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        raise RuntimeError(f"config.json unvollständig. Fehlende Felder: {', '.join(missing)}")

    return AppConfig(
        bose_ip=str(data["bose_ip"]).strip(),
        soundcork_base=str(data["soundcork_base"]).rstrip("/"),
        soundcork_dir=Path(str(data["soundcork_dir"])),
        backup_dir=Path(str(data["backup_dir"])),
        account_id=str(data.get("account_id", "")).strip(),
        restart_soundcork_after_save=bool(data.get("restart_soundcork_after_save", True)),
        docker_compose_file=str(data.get("docker_compose_file", "")).strip(),
        docker_service_name=str(data.get("docker_service_name", "soundcork")).strip() or "soundcork",
        request_timeout_seconds=int(data.get("request_timeout_seconds", 12)),
    )


def http_get_text(url: str, timeout: int) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def http_post_xml(url: str, xml_body: str, timeout: int) -> str:
    data = xml_body.encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def content_item_xml(name: str, location: str, art: str, item_type: str = "stationurl") -> str:
    return (
        f'<ContentItem source="TUNEIN" type="{escape(item_type)}" '
        f'location="{escape(location)}" sourceAccount="" isPresetable="true">'
        f'<itemName>{escape(name)}</itemName>'
        f'<containerArt>{escape(art or "")}</containerArt>'
        f'</ContentItem>'
    )


def preset_xml(slot: str, name: str, location: str, art: str, item_type: str = "stationurl") -> str:
    return (
        f'<preset id="{escape(str(slot))}">\n'
        f'  {content_item_xml(name=name, location=location, art=art, item_type=item_type)}\n'
        f'</preset>\n'
    )


def load_presets(config: AppConfig) -> list[dict[str, str]]:
    xml_text = http_get_text(f"{config.bose_base}/presets", config.request_timeout_seconds)
    root = ET.fromstring(xml_text)

    presets: list[dict[str, str]] = []
    for preset in root.findall("preset"):
        slot = preset.attrib.get("id", "?")
        item = preset.find("ContentItem")

        if item is None:
            presets.append(
                {
                    "slot": slot,
                    "name": "(leer)",
                    "source": "",
                    "location": "",
                    "art": "",
                    "type": "",
                    "content_xml": "",
                }
            )
            continue

        name_el = item.find("itemName")
        art_el = item.find("containerArt")
        content_xml = ET.tostring(item, encoding="unicode")

        presets.append(
            {
                "slot": slot,
                "name": name_el.text if name_el is not None and name_el.text else "(ohne Name)",
                "source": item.attrib.get("source", ""),
                "location": item.attrib.get("location", ""),
                "art": art_el.text if art_el is not None and art_el.text else "",
                "type": item.attrib.get("type", ""),
                "content_xml": content_xml,
            }
        )

    presets.sort(key=lambda p: int(p["slot"]) if p["slot"].isdigit() else 99)
    return presets


def search_tunein(config: AppConfig, query: str) -> list[dict[str, str]]:
    q = urllib.parse.quote_plus(query.strip())
    url = f"{config.soundcork_search}?q={q}"
    text = http_get_text(url, config.request_timeout_seconds)
    data = json.loads(text)

    results: list[dict[str, str]] = []
    for section in data.get("bmx_sections", []):
        if section.get("name") != "Stations":
            continue

        for item in section.get("items", []):
            preset = item.get("_links", {}).get("bmx_preset", {})
            name = preset.get("name") or item.get("name") or ""
            location = preset.get("href") or ""
            item_type = preset.get("type") or ""
            art = preset.get("containerArt") or item.get("imageUrl") or ""
            subtitle = item.get("subtitle") or ""

            if not name or not location:
                continue
            if item_type != "stationurl":
                continue

            results.append(
                {
                    "name": name,
                    "location": location,
                    "type": item_type,
                    "art": art,
                    "subtitle": subtitle,
                }
            )

    return results


def zip_directory(source_dir: Path, destination_zip: Path) -> None:
    source_dir = source_dir.resolve()
    destination_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob("*"):
            # Avoid nesting accidental backup archives if backup_dir is inside source_dir.
            try:
                if destination_zip.resolve() == path.resolve():
                    continue
            except FileNotFoundError:
                pass
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def make_full_backup(config: AppConfig) -> str:
    stamp = now_stamp()
    backup_zip = config.backup_dir / f"soundcork_BACKUP_BEFORE_PRESET_CHANGE_{stamp}.zip"
    zip_directory(config.soundcork_dir, backup_zip)
    log(f"Backup erstellt: {backup_zip}")
    return str(backup_zip)


def find_soundcork_presets_xml(config: AppConfig) -> Path | None:
    if config.account_id:
        candidate = config.soundcork_dir / "data" / config.account_id / "Presets.xml"
        if candidate.exists() or candidate.parent.exists():
            return candidate

    data_dir = config.soundcork_dir / "data"
    if not data_dir.exists():
        return None

    candidates = sorted(data_dir.glob("*/Presets.xml"))
    if candidates:
        return candidates[0]

    return None


def sync_soundcork_presets_after_store(config: AppConfig) -> str:
    stamp = now_stamp()
    xml_text = http_get_text(f"{config.bose_base}/presets", config.request_timeout_seconds)
    PROOF_DIR.mkdir(parents=True, exist_ok=True)

    proof_file = PROOF_DIR / f"presets_after_store_{stamp}.xml"
    proof_file.write_text(xml_text, encoding="utf-8")

    soundcork_presets_xml = find_soundcork_presets_xml(config)
    if soundcork_presets_xml is not None:
        soundcork_presets_xml.parent.mkdir(parents=True, exist_ok=True)
        soundcork_presets_xml.write_text(xml_text, encoding="utf-8")
        log(f"SoundCork Presets.xml aktualisiert: {soundcork_presets_xml}")
    else:
        log("SoundCork Presets.xml nicht gefunden; Sync übersprungen.")

    log(f"Presets nach Store gesichert: {proof_file}")
    return str(proof_file)


def restart_soundcork(config: AppConfig) -> str:
    if not config.restart_soundcork_after_save:
        log("SoundCork restart deaktiviert.")
        return "SoundCork restart deaktiviert."

    compose_file = config.compose_file
    if not compose_file.exists():
        msg = f"docker-compose.yml nicht gefunden: {compose_file}. Restart übersprungen."
        log(msg)
        return msg

    cmd = ["docker", "compose", "-f", str(compose_file), "restart", config.docker_service_name]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    log(f"SoundCork restart returncode={result.returncode}: {output.strip()}")

    if result.returncode != 0:
        raise RuntimeError(f"SoundCork Neustart fehlgeschlagen:\n{output}")

    return output.strip()


class PresetEditorApp:
    def __init__(self, root: tk.Tk, config: AppConfig):
        self.root = root
        self.config = config
        self.root.title(f"{APP_NAME} – V{APP_VERSION}")
        self.root.geometry("1220x760")
        self.root.minsize(1080, 690)

        self.status_var = tk.StringVar(value="Bereit.")
        self.search_var = tk.StringVar(value="")
        self.slot_var = tk.StringVar(value="6")
        self.cards: list[dict[str, ttk.Widget]] = []
        self.presets: list[dict[str, str]] = []
        self.search_results: list[dict[str, str]] = []

        self.build_ui()
        self.refresh()

    def build_ui(self) -> None:
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")

        title = ttk.Label(header, text="Bose SoundTouch – Radio Preset Editor", font=("Segoe UI", 17, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            header,
            text=f"Bose: {self.config.bose_ip}   |   SoundCork: {self.config.soundcork_base}   |   V{APP_VERSION}",
            font=("Segoe UI", 9),
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        controls = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        controls.pack(fill="x")
        ttk.Button(controls, text="Presets neu laden", command=self.refresh).pack(side="left")
        ttk.Button(controls, text="SoundCork Status prüfen", command=self.check_soundcork).pack(side="left", padx=(8, 0))

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        preset_area = ttk.LabelFrame(main, text="Aktuelle Presets", padding=10)
        preset_area.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        for row in range(3):
            preset_area.rowconfigure(row, weight=1)
        for col in range(2):
            preset_area.columnconfigure(col, weight=1)

        for i in range(6):
            frame = ttk.LabelFrame(preset_area, text=f"Preset {i + 1}", padding=10)
            frame.grid(row=i // 2, column=i % 2, sticky="nsew", padx=7, pady=7)
            frame.columnconfigure(0, weight=1)

            name = ttk.Label(frame, text="...", font=("Segoe UI", 12, "bold"), wraplength=310)
            name.grid(row=0, column=0, sticky="w", pady=(0, 6))

            play_btn = ttk.Button(frame, text="ABSPIELEN", command=lambda idx=i: self.play_preset(idx))
            play_btn.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipady=6)

            source = ttk.Label(frame, text="", font=("Consolas", 9))
            source.grid(row=2, column=0, sticky="w")

            location = ttk.Label(frame, text="", font=("Consolas", 8), wraplength=310)
            location.grid(row=3, column=0, sticky="w", pady=(3, 0))

            self.cards.append({"frame": frame, "name": name, "source": source, "location": location, "play_btn": play_btn})

        search_area = ttk.LabelFrame(main, text="TuneIn-Suche und Speichern", padding=10)
        search_area.grid(row=0, column=1, sticky="nsew")
        search_area.columnconfigure(0, weight=1)
        search_area.rowconfigure(3, weight=1)

        ttk.Label(search_area, text="Sender suchen:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")

        search_row = ttk.Frame(search_area)
        search_row.grid(row=1, column=0, sticky="ew", pady=(6, 8))
        search_row.columnconfigure(0, weight=1)

        entry = ttk.Entry(search_row, textvariable=self.search_var)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<Return>", lambda event: self.run_search())
        ttk.Button(search_row, text="Suchen", command=self.run_search).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(
            search_area,
            text="Nur echte Stationen werden angezeigt. Shows/Podcasts werden ignoriert.",
            font=("Segoe UI", 8),
        ).grid(row=2, column=0, sticky="w", pady=(0, 6))

        list_frame = ttk.Frame(search_area)
        list_frame.grid(row=3, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.result_list = tk.Listbox(list_frame, height=16)
        self.result_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.result_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_list.configure(yscrollcommand=scrollbar.set)
        self.result_list.bind("<Double-Button-1>", lambda event: self.play_selected_search_result())
        self.result_list.bind("<<ListboxSelect>>", lambda event: self.update_result_detail())

        self.detail_var = tk.StringVar(value="Kein Suchergebnis ausgewählt.")
        detail = ttk.Label(search_area, textvariable=self.detail_var, wraplength=400, font=("Segoe UI", 9))
        detail.grid(row=4, column=0, sticky="ew", pady=(8, 8))

        ttk.Button(search_area, text="SUCHERGEBNIS PROBE ABSPIELEN", command=self.play_selected_search_result).grid(
            row=5, column=0, sticky="ew", ipady=8
        )

        save_area = ttk.LabelFrame(search_area, text="Auf Hardware-Preset speichern", padding=10)
        save_area.grid(row=6, column=0, sticky="ew", pady=(12, 0))
        save_area.columnconfigure(1, weight=1)

        ttk.Label(save_area, text="Slot:").grid(row=0, column=0, sticky="w")
        slot_box = ttk.Combobox(save_area, textvariable=self.slot_var, values=["1", "2", "3", "4", "5", "6"], width=5, state="readonly")
        slot_box.grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Button(save_area, text="AUSWAHL AUF SLOT SPEICHERN", command=self.save_selected_result_to_slot).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0), ipady=8
        )
        ttk.Label(save_area, text="Vor dem Speichern wird automatisch ein ZIP-Backup erstellt.", font=("Segoe UI", 8)).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        status = ttk.Label(self.root, textvariable=self.status_var, padding=10)
        status.pack(fill="x")

    def refresh(self) -> None:
        try:
            self.presets = load_presets(self.config)
            log("Presets geladen.")
            for i, card in enumerate(self.cards):
                if i < len(self.presets):
                    p = self.presets[i]
                    card["frame"].configure(text=f"Preset {p['slot']}")
                    card["name"].configure(text=p["name"])
                    card["source"].configure(text=f"{p['source']} / {p['type']}")
                    card["location"].configure(text=p["location"])
                    card["play_btn"].configure(state="normal" if p["content_xml"] else "disabled")
                else:
                    card["frame"].configure(text=f"Preset {i + 1}")
                    card["name"].configure(text="(leer)")
                    card["source"].configure(text="")
                    card["location"].configure(text="")
                    card["play_btn"].configure(state="disabled")
            self.status_var.set(f"Presets geladen: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            log(f"FEHLER beim Laden: {e}")
            self.status_var.set("Fehler beim Laden der Presets.")
            messagebox.showerror("Fehler", f"Presets konnten nicht geladen werden:\n\n{e}")

    def play_xml(self, xml_body: str, label: str) -> None:
        response = http_post_xml(f"{self.config.bose_base}/select", xml_body, self.config.request_timeout_seconds)
        log(f"Abgespielt: {label} / Antwort: {response[:120]}")
        self.status_var.set(f"Abgespielt: {label}")

    def play_preset(self, index: int) -> None:
        if index >= len(self.presets):
            return
        preset = self.presets[index]
        if not preset.get("content_xml"):
            messagebox.showwarning("Preset leer", "Dieses Preset enthält keinen abspielbaren Inhalt.")
            return
        try:
            self.status_var.set(f"Spiele Preset {preset['slot']}: {preset['name']} ...")
            self.root.update_idletasks()
            self.play_xml(preset["content_xml"], f"Preset {preset['slot']} – {preset['name']}")
        except Exception as e:
            log(f"FEHLER beim Abspielen von Preset {preset.get('slot')}: {e}")
            self.status_var.set("Fehler beim Abspielen.")
            messagebox.showerror("Abspielen fehlgeschlagen", f"Preset konnte nicht abgespielt werden:\n\n{e}")

    def run_search(self) -> None:
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Suche leer", "Bitte einen Sendernamen eingeben.")
            return
        try:
            self.status_var.set(f"Suche nach: {query} ...")
            self.root.update_idletasks()
            self.search_results = search_tunein(self.config, query)
            self.result_list.delete(0, tk.END)
            for result in self.search_results:
                subtitle = f" — {result['subtitle']}" if result.get("subtitle") else ""
                self.result_list.insert(tk.END, f"{result['name']}{subtitle}")
            if self.search_results:
                self.result_list.selection_set(0)
                self.update_result_detail()
                self.status_var.set(f"{len(self.search_results)} Stationen gefunden.")
                log(f"Suche '{query}' ergab {len(self.search_results)} Stationen.")
            else:
                self.detail_var.set("Keine Station gefunden.")
                self.status_var.set("Keine Station gefunden.")
                log(f"Suche '{query}' ergab keine Stationen.")
        except Exception as e:
            log(f"FEHLER bei Suche '{query}': {e}")
            self.status_var.set("Fehler bei der Suche.")
            messagebox.showerror("Suche fehlgeschlagen", f"Die Suche ist fehlgeschlagen:\n\n{e}")

    def selected_result(self) -> dict[str, str] | None:
        selection = self.result_list.curselection()
        if not selection:
            return None
        idx = selection[0]
        if idx >= len(self.search_results):
            return None
        return self.search_results[idx]

    def update_result_detail(self) -> None:
        result = self.selected_result()
        if not result:
            self.detail_var.set("Kein Suchergebnis ausgewählt.")
            return
        self.detail_var.set(
            f"Name: {result['name']}\n"
            f"Location: {result['location']}\n"
            f"Typ: {result['type']}\n"
            f"Logo: {result['art']}"
        )

    def play_selected_search_result(self) -> None:
        result = self.selected_result()
        if not result:
            messagebox.showwarning("Kein Ergebnis", "Bitte zuerst ein Suchergebnis auswählen.")
            return
        try:
            xml = content_item_xml(name=result["name"], location=result["location"], art=result["art"], item_type=result["type"])
            self.status_var.set(f"Probe-Abspielen: {result['name']} ...")
            self.root.update_idletasks()
            self.play_xml(xml, f"Suchergebnis – {result['name']}")
        except Exception as e:
            log(f"FEHLER beim Probe-Abspielen von {result.get('name')}: {e}")
            self.status_var.set("Fehler beim Probe-Abspielen.")
            messagebox.showerror("Probe-Abspielen fehlgeschlagen", f"Sender konnte nicht abgespielt werden:\n\n{e}")

    def save_selected_result_to_slot(self) -> None:
        result = self.selected_result()
        if not result:
            messagebox.showwarning("Kein Ergebnis", "Bitte zuerst ein Suchergebnis auswählen.")
            return
        slot = self.slot_var.get().strip()
        if slot not in {"1", "2", "3", "4", "5", "6"}:
            messagebox.showwarning("Ungültiger Slot", "Bitte Slot 1 bis 6 wählen.")
            return
        confirm = messagebox.askyesno(
            "Preset speichern?",
            f"Soll folgender Sender auf Hardware-Preset {slot} gespeichert werden?\n\n"
            f"{result['name']}\n{result['location']}\n\n"
            f"Vorher wird automatisch ein Backup erstellt.",
        )
        if not confirm:
            return
        try:
            self.status_var.set("Erstelle Backup ...")
            self.root.update_idletasks()
            backup_zip = make_full_backup(self.config)

            xml = preset_xml(slot=slot, name=result["name"], location=result["location"], art=result["art"], item_type=result["type"])
            PROOF_DIR.mkdir(parents=True, exist_ok=True)
            body_file = PROOF_DIR / f"storePreset_slot{slot}_{now_stamp()}.xml"
            body_file.write_text(xml, encoding="utf-8")

            self.status_var.set(f"Speichere {result['name']} auf Preset {slot} ...")
            self.root.update_idletasks()
            response = http_post_xml(f"{self.config.bose_base}/storePreset", xml, self.config.request_timeout_seconds)
            log(f"storePreset Slot {slot}: {result['name']} / Antwort: {response[:160]}")

            self.status_var.set("Synchronisiere SoundCork Presets.xml ...")
            self.root.update_idletasks()
            proof_after = sync_soundcork_presets_after_store(self.config)

            self.status_var.set("Starte SoundCork neu ...")
            self.root.update_idletasks()
            restart_msg = restart_soundcork(self.config)

            self.status_var.set("Lade Presets neu ...")
            self.root.update_idletasks()
            self.refresh()

            messagebox.showinfo(
                "Gespeichert",
                f"Preset {slot} wurde gespeichert:\n\n"
                f"{result['name']}\n\n"
                f"Backup:\n{backup_zip}\n\n"
                f"Preset-Sicherung:\n{proof_after}\n\n"
                f"SoundCork:\n{restart_msg[:600]}",
            )
            self.status_var.set(f"Gespeichert: Preset {slot} – {result['name']}")
        except Exception as e:
            log(f"FEHLER beim Speichern auf Slot {slot}: {e}")
            self.status_var.set("Fehler beim Speichern.")
            messagebox.showerror("Speichern fehlgeschlagen", f"Preset konnte nicht gespeichert werden:\n\n{e}")

    def check_soundcork(self) -> None:
        try:
            text = http_get_text(self.config.soundcork_admin, self.config.request_timeout_seconds)
            if text:
                self.status_var.set("SoundCork Admin erreichbar.")
                log("SoundCork Admin erreichbar.")
                messagebox.showinfo("SoundCork", "SoundCork Admin ist erreichbar.")
            else:
                self.status_var.set("SoundCork antwortet leer.")
                messagebox.showwarning("SoundCork", "SoundCork antwortet leer.")
        except Exception as e:
            log(f"SoundCork Check Fehler: {e}")
            self.status_var.set("SoundCork nicht erreichbar.")
            messagebox.showerror("SoundCork", f"SoundCork nicht erreichbar:\n\n{e}")


def main() -> None:
    try:
        config = load_config()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Konfiguration fehlt", str(e))
        print(e, file=sys.stderr)
        sys.exit(1)

    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Editor V{APP_VERSION} gestartet.")
    root = tk.Tk()
    PresetEditorApp(root, config)
    root.mainloop()
    log("Editor beendet.")


if __name__ == "__main__":
    main()
