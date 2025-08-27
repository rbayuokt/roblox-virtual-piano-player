from __future__ import annotations
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vp import __version__ as VERSION
from vp.model import (
    SongSettings,
    Event,
    TokenEvent,
    RestEvent,
    is_newline,
    PrintMode,
)
from vp.engine.timing import step_duration, split_hold_gap, BeatClock


class Player:
    def __init__(
        self,
        backend,
        *,
        default_print_mode: PrintMode = "cumulative",
        print_last_n: int = 24,
        divider: str = "—",
        console: Console | None = None,
    ) -> None:
        self.backend = backend
        self.default_print_mode = default_print_mode
        self.print_last_n = max(1, int(print_last_n))
        self.divider = divider
        self.console = console or Console()

    def _join_last_n(self, toks: List[str]) -> str:
        if len(toks) <= self.print_last_n:
            return " ".join(toks)
        return " ".join(toks[-self.print_last_n :])

    def _print_token(
        self,
        mode: PrintMode,
        current_text: str,
        line_tokens: List[str],
        global_tokens: List[str],
    ) -> None:
        if mode == "off":
            return
        if mode == "current":
            self.console.print(current_text, highlight=False)
            return
        if mode == "cumulative":
            self.console.print(self._join_last_n(line_tokens), highlight=False)
            return
        if mode == "both":
            self.console.print(current_text, highlight=False)
            self.console.print(self._join_last_n(global_tokens), highlight=False)
            return
        self.console.print(current_text, highlight=False)
        self.console.print(self._join_last_n(line_tokens), highlight=False)

    def preview(self, settings: SongSettings, file_name: str, total_steps: int, note_steps: int) -> None:
        table = Table.grid(expand=False)
        table.add_row(f"[bold]{settings.title}[/bold]")
        meta = Table.grid()
        if settings.author:
            meta.add_row(f"[b]Author:[/b] {settings.author}")
        meta.add_row(f"[b]File:[/b] {file_name}")
        meta.add_row(f"[b]Tempo:[/b] {settings.bpm} BPM × SUBDIV {settings.subdiv}")
        meta.add_row(f"[b]Start Delay:[/b] {settings.start_delay:.1f}s")
        meta.add_row(f"[b]Chord Hold:[/b] {settings.chord_hold:.2f}")
        meta.add_row(f"[b]Steps:[/b] {total_steps}  (notes/chords: {note_steps})")
        table.add_row(meta)
        self.console.print(Panel(table, title=f"Virtual Piano Player v{VERSION}", expand=False))

    def countdown(self, seconds: float) -> None:
        seconds = max(0.0, float(seconds))
        if seconds <= 0:
            return
        self.console.print(f"[dim]Focus Roblox. Starting in {seconds:.1f}s…[/dim]")
        for i in range(int(seconds), 0, -1):
            self.console.print(f"{i}", end=" ", highlight=False)
            self.console.file.flush()
            from time import sleep
            sleep(1)
        self.console.print("\n[green]Go![/green]")

    def play(self, settings: SongSettings, events: List[Event], *, file_name: str = "") -> None:
        step_secs = step_duration(settings.bpm, settings.subdiv)
        hold_secs, _ = split_hold_gap(step_secs, settings.chord_hold)
        mode: PrintMode = settings.print_mode or self.default_print_mode

        note_steps = sum(1 for e in events if isinstance(e, TokenEvent))
        total_steps = sum(
            (e.steps if isinstance(e, RestEvent) else 1)
            for e in events
            if not is_newline(e)
        )

        if file_name:
            self.preview(settings, file_name, total_steps, note_steps)

        clock = BeatClock(step_secs=step_secs, start_delay=settings.start_delay)
        t0 = clock.start_time()

        self.countdown(settings.start_delay)

        line_tokens: List[str] = []
        global_tokens: List[str] = []
        step_index = 0

        for e in events:
            if is_newline(e):
                line_tokens = []
                self.console.print(self.divider, highlight=False)
                continue

            if isinstance(e, RestEvent):
                for _ in range(e.steps):
                    clock.sleep_until_step(t0, step_index)
                    token_text = "·"
                    line_tokens.append(token_text)
                    global_tokens.append(token_text)
                    self._print_token(mode, token_text, line_tokens, global_tokens)
                    step_index += 1
                    if step_index % 50 == 0:
                        self.console.print(f"[dim]...played {step_index} / {total_steps}[/dim]")
                continue

            clock.sleep_until_step(t0, step_index)

            token_text = e.text
            line_tokens.append(token_text)
            global_tokens.append(token_text)

            self._print_token(mode, token_text, line_tokens, global_tokens)

            self.backend.press(e.keys, hold_secs)

            step_index += 1
            if step_index % 50 == 0:
                self.console.print(f"[dim]...played {step_index} / {total_steps}[/dim]")

        if step_index != total_steps:
            self.console.print(f"[dim]...played {step_index} / {total_steps}[/dim]")
        self.console.print("[bold green]Done.[/bold green]")
