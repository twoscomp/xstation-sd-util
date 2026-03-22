from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterator

from rich.console import Console

from .config import SYSTEM_FOLDER
from .extractors.base import apply_single_folder_strip, get_extractor
from .organizer import alpha_folder
from .sources.base import ArchiveEntry, GameSource

console = Console()


def _dest_path(dest: Path, stem: str) -> Path:
    return dest / alpha_folder(stem) / stem


def _is_non_empty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def _fmt_bytes(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} GB"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.1f} KB"
    return f"{n} B"


def _space_check(
    pending: list[ArchiveEntry],
    dest: Path,
    is_smb: bool,
) -> None:
    n = len(pending)
    game_word = "game" if n == 1 else "games"

    total = 0
    all_unknown = True

    for entry in pending:
        size = -1
        if not is_smb and entry.local_path() is not None:
            try:
                size = int(get_extractor(entry.suffix).uncompressed_size(entry.local_path()))  # type: ignore[arg-type]
            except Exception:
                size = -1

        if size == -1:
            # Fall back to compressed size as lower bound
            if entry.size >= 0:
                size = entry.size
            else:
                size = 0
        else:
            all_unknown = False

        total += size

    if all_unknown and total == 0:
        console.print(f"[bold]{n} {game_word} to extract[/bold]  ·  space needed: unknown")
        return

    free = shutil.disk_usage(dest).free
    needed_str = _fmt_bytes(total)
    free_str = _fmt_bytes(free)

    if free >= total:
        console.print(
            f"[bold]{n} {game_word} to extract[/bold]  ·  "
            f"need ~{needed_str}, available {free_str} [green]✓[/green]"
        )
    else:
        console.print(
            f"[bold]{n} {game_word} to extract[/bold]  ·  "
            f"need ~{needed_str}, available {free_str} [yellow]— may be insufficient[/yellow]"
        )


def process(
    source: GameSource,
    dest: Path,
    dry_run: bool = False,
    skip_existing: bool = True,
    verbose: bool = False,
    temp_dir: Path | None = None,
    yes: bool = False,
) -> None:
    tmp_base = temp_dir or (dest / ".xstation_tmp")
    tmp_base.mkdir(parents=True, exist_ok=True)

    is_smb = _is_smb_source(source)

    entries = list(source.list_archives())
    if not entries:
        console.print("[yellow]No archives found in source.[/yellow]")
        return

    pending = [
        e for e in entries
        if not (skip_existing and _is_non_empty(_dest_path(dest, e.stem)))
        and e.stem != SYSTEM_FOLDER
    ]

    if not pending:
        console.print("[yellow]Nothing to extract.[/yellow]")
        return

    _space_check(pending, dest, is_smb)

    if dry_run:
        console.print("[dim](dry run — no changes will be made)[/dim]")
    elif not yes:
        reply = console.input("[bold]Proceed?[/bold] [y/N] ").strip().lower()
        if reply not in ("y", "yes"):
            console.print("[yellow]Aborted.[/yellow]")
            return

    for entry in entries:
        game_dest = _dest_path(dest, entry.stem)

        # Guard: never touch the system folder
        if game_dest.parts and game_dest.name == SYSTEM_FOLDER:
            console.print(f"[yellow]Skipping reserved name: {entry.stem}[/yellow]")
            continue

        if skip_existing and _is_non_empty(game_dest):
            console.print(f"[dim]Skipping (exists): {entry.stem}[/dim]")
            continue

        if dry_run:
            folder = alpha_folder(entry.stem)
            console.print(f"[cyan]Would extract:[/cyan] {entry.stem!r} → {folder}/{entry.stem}/")
            continue

        console.print(f"[green]Extracting:[/green] {entry.stem}")
        tmp_game_dir = tmp_base / entry.stem

        try:
            tmp_game_dir.mkdir(parents=True, exist_ok=True)

            # Resolve archive path (download for SMB)
            if is_smb:
                archive_path = source.download(entry, tmp_base)  # type: ignore[attr-defined]
                cleanup_archive = True
            else:
                archive_path = entry.local_path()
                assert archive_path is not None
                cleanup_archive = False

            extractor = get_extractor(entry.suffix)
            extractor.extract(archive_path, tmp_game_dir, verbose=verbose)

            if cleanup_archive:
                archive_path.unlink(missing_ok=True)

            apply_single_folder_strip(tmp_game_dir)

            game_dest.parent.mkdir(parents=True, exist_ok=True)
            if game_dest.exists():
                shutil.rmtree(game_dest)
            os.rename(tmp_game_dir, game_dest)

        except Exception as exc:
            console.print(f"[red]Error extracting {entry.stem!r}: {exc}[/red]")
            if tmp_game_dir.exists():
                shutil.rmtree(tmp_game_dir, ignore_errors=True)


def _is_smb_source(source: GameSource) -> bool:
    return hasattr(source, "download")
