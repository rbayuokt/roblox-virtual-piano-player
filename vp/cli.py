from __future__ import annotations
from pathlib import Path
from typing import List, Tuple

from rich.console import Console
from rich.panel import Panel

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.containers import WindowAlign
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Button, Dialog, RadioList, Label

from vp.parser import list_sheets, load_sheet
from vp.player import Player
from vp.keys.pyautogui_backend import PyAutoGUIBackend

PICKER_STYLE = Style.from_dict({
    "dialog":          "bg:#000000 #ffffff",
    "dialog.body":     "bg:#000000 #ffffff",
    "dialog shadow":   "bg:#000000",
    "frame.label":     "bg:#000000 #00ff99",
    "radio":           "bg:#000000 #ffffff",
    "radio-checked":   "bg:#000000 #00ff99",
    "button":          "bg:#111111 #ffffff",
    "button.focused":  "bg:#333333 #00ff99",
    "footer":          "bg:#000000 #888888",
})

FOOTER_TEXT = "created by: @rbayuokt"

def _radiolist_with_footer(
    *,
    title: str,
    text: str,
    values: List[Tuple[str, str]],
    default_value: str | None,
    ok_text: str = "OK",
    cancel_text: str = "Cancel",
    style: Style | None = None,
) -> str | None:
    radio = RadioList(values)
    if default_value is not None:
        radio.current_value = default_value

    def accept() -> None:
        get_app().exit(result=radio.current_value)

    def cancel() -> None:
        get_app().exit(result=None)

    ok_button = Button(text=ok_text, handler=accept)
    cancel_button = Button(text=cancel_text, handler=cancel)

    footer_window = Window(
        content=FormattedTextControl(FOOTER_TEXT),
        height=1,
        style="class:footer",
        align=WindowAlign.CENTER,
    )

    body = HSplit(
        [
            Label(text),
            radio,
            Window(height=1, char=" "),
            footer_window,
        ],
        padding=1,
        width=D(preferred=80),
    )

    dialog = Dialog(
        title=title,
        body=body,
        buttons=[ok_button, cancel_button],
        with_background=True,
    )

    kb = KeyBindings()

    @kb.add("enter", eager=True)
    @kb.add("c-m", eager=True)
    @kb.add("c-j", eager=True)
    def _enter(event) -> None:
        accept()

    @kb.add("escape")
    def _esc(event) -> None:
        cancel()

    app = Application(
        layout=Layout(dialog, focused_element=radio),
        key_bindings=kb,
        style=style or PICKER_STYLE,
        full_screen=True,
        mouse_support=True,
    )
    return app.run()

def pick_sheet(sheets_dir: str, console: Console) -> Path | None:
    paths = list_sheets(sheets_dir)
    if not paths:
        console.print(
            Panel.fit(
                f"No sheets found in '{sheets_dir}'.\n"
                "Add .txt or .vps files with a header like:\n"
                "TITLE=My Song\nBPM=97\nSUBDIV=4\nSTART_DELAY=5.0\nCHORD_HOLD=0.75\n\n"
                "t r w ...",
                title="No Sheets",
                border_style="red",
                style="on black",
            )
        )
        return None

    choices: List[Tuple[str, str]] = []
    for p in paths:
        try:
            settings, _ = load_sheet(p)
            label = f"{settings.title}  ·  {p.name}  ·  {settings.bpm} BPM × {settings.subdiv}"
        except Exception:
            label = f"{p.name}"
        choices.append((str(p), label))

    default_value = choices[0][0]

    result = _radiolist_with_footer(
        title="Roblox VP Player",
        text="Use ↑/↓ to select a song. Press ENTER to play.",
        values=choices,
        default_value=default_value,
        ok_text="Play",
        cancel_text="Quit",
        style=PICKER_STYLE,
    )
    console.clear()
    if result is None:
        return None
    return Path(result)

def main(
    sheets_dir: str = "sheets",
    *,
    default_print_mode: str = "cumulative",
    print_last_n: int = 24,
    panic_hotcorner: bool = True,
) -> None:
    console = Console()
    while True:
        path = pick_sheet(sheets_dir, console)
        if path is None:
            break
        try:
            settings, events = load_sheet(path)
        except Exception as e:
            console.print(f"[red]Failed to load sheet:[/red] {e}")
            continue
        backend = PyAutoGUIBackend(panic_hotcorner=panic_hotcorner)
        player = Player(
            backend,
            default_print_mode=default_print_mode,
            print_last_n=print_last_n,
            console=console,
        )
        player.play(settings, events, file_name=path.name)
        console.print()
        console.print(
            "Press [b]ENTER[/b] to pick another song or type [b]q[/b] then ENTER to quit.",
            style="dim on black",
        )
        try:
            user = input().strip().lower()
        except KeyboardInterrupt:
            break
        if user == "q":
            break
