from __future__ import annotations
import re
from pathlib import Path
from typing import List, Tuple, Union

from vp.model import SongSettings, TokenEvent, RestEvent, Event

_ALLOWED_EXTS = {".txt", ".vps"}
_HEADER_KV_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$")
_ALNUM_RE = re.compile(r"[A-Za-z0-9]")

_BRACKET_TRANS = str.maketrans({
    "［": "[", "【": "[", "〖": "[", "〔": "[", "｛": "[", "〈": "[", "«": "[", "「": "[", "『": "[", "⟦": "[", "⟮": "[",
    "］": "]", "】": "]", "〗": "]", "〕": "]", "｝": "]", "〉": "]", "»": "]", "」": "]", "』": "]", "⟧": "]", "⟯": "]",
})
_ZW_REMOVE = ("\u200b", "\u200c", "\u200d", "\ufeff", "\u2060", "\u180e", "\u00ad")
_NBSP_TO_SPACE = ("\u00a0", "\u202f", "\u2007")

def _normalize_notation(s: str) -> str:
    s = s.translate(_BRACKET_TRANS)
    for ch in _ZW_REMOVE:
        s = s.replace(ch, "")
    for ch in _NBSP_TO_SPACE:
        s = s.replace(ch, " ")
    return s

def _coerce_settings(key: str, val: str, s: SongSettings) -> None:
    k = key.strip().upper()
    v = val.strip()
    try:
        if k == "TITLE":
            s.title = v
        elif k == "AUTHOR":
            s.author = v
        elif k == "BPM":
            s.bpm = int(v)
        elif k == "SUBDIV":
            s.subdiv = int(v)
        elif k == "START_DELAY":
            s.start_delay = float(v)
        elif k == "CHORD_HOLD":
            s.chord_hold = float(v)
        elif k == "PRINT_MODE":
            pm = v.lower()
            if pm in ("paired", "current", "cumulative", "both", "off"):
                s.print_mode = pm
    except ValueError:
        pass

def parse_sheet_text(sheet_text: str) -> Tuple[SongSettings, List[Event]]:
    text = sheet_text.replace("\r\n", "\n").replace("\r", "\n")
    parts = text.split("\n\n", 1)
    header_block = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    settings = SongSettings()
    header_looked_like_kv = False
    for line in header_block.splitlines():
        raw = line.rstrip("\n")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        m = _HEADER_KV_RE.match(raw)
        if m:
            header_looked_like_kv = True
            _coerce_settings(m.group(1), m.group(2), settings)
        else:
            header_looked_like_kv = False
            settings = SongSettings()
            body = text
            break

    notation = _normalize_notation(body if header_looked_like_kv else body)

    events: List[Event] = []
    i = 0
    last_was_newline = False
    n = len(notation)

    while i < n:
        c = notation[i]
        if c == '[':
            j = notation.find(']', i + 1)
            if j == -1:
                i += 1
                continue
            inside = notation[i + 1 : j]
            display_inside = "".join(_ALNUM_RE.findall(inside))
            if display_inside:
                keys = [k.lower() for k in display_inside]
                events.append(TokenEvent(keys=keys, text=f"[{display_inside}]"))
                last_was_newline = False
            i = j + 1
        elif c == '.':
            j = i
            while j < n and notation[j] == '.':
                j += 1
            steps = j - i
            if steps > 0:
                events.append(RestEvent(steps=steps, text='.' * steps))
                last_was_newline = False
            i = j
        elif c == '\n':
            if not last_was_newline:
                events.append({"newline": True})
                last_was_newline = True
            i += 1
        elif c.isalnum():
            events.append(TokenEvent(keys=[c.lower()], text=c))
            last_was_newline = False
            i += 1
        else:
            i += 1
    return settings, events

def load_sheet(path: Union[str, Path]) -> Tuple[SongSettings, List[Event]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    if p.suffix.lower() not in _ALLOWED_EXTS:
        raise ValueError(f"Unsupported extension {p.suffix}. Use one of: {sorted(_ALLOWED_EXTS)}")
    return parse_sheet_text(p.read_text(encoding="utf-8"))

def list_sheets(folder: Union[str, Path]) -> List[Path]:
    root = Path(folder)
    if not root.exists():
        return []
    files = [f for f in root.iterdir() if f.is_file() and f.suffix.lower() in _ALLOWED_EXTS]
    return sorted(files, key=lambda x: x.name.lower())
