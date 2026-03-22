from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


def _check_smb_available() -> None:
    try:
        import smbclient  # noqa: F401
    except ImportError:
        console.print(
            "[red]SMB support requires:[/red] pip install \"xstation-sd-util[smb]\""
        )
        sys.exit(1)


def _check_rar_tool(source_dir: Path | None, is_smb: bool) -> None:
    """Check for unrar/bsdtar if RAR archives are present."""
    has_rar = False
    if source_dir is not None:
        has_rar = any(source_dir.glob("*.rar"))
    # For SMB we can't easily pre-check; the extractor will fail fast anyway.
    if has_rar:
        if shutil.which("unrar") is None and shutil.which("bsdtar") is None:
            console.print(
                "[red]RAR archives found but 'unrar' is not installed.[/red]\n"
                "Install with: [bold]apt install unrar[/bold]  /  [bold]brew install rar[/bold]"
            )
            sys.exit(1)


@click.command()
@click.argument("source")
@click.argument("dest", type=click.Path())
@click.option("-n", "--dry-run", is_flag=True, help="Show what would happen, don't extract.")
@click.option(
    "--no-skip-existing",
    "no_skip_existing",
    is_flag=True,
    default=False,
    help="Re-extract even if folder exists (skip is ON by default).",
)
@click.option("-f", "--filter", "glob_filter", default=None, help="Only process archives matching pattern.")
@click.option("--smb-username", default=None, help="SMB username (overrides URL).")
@click.option("--smb-password", default=None, help="SMB password (prompted if omitted).")
@click.option("--smb-domain", default=None, help="SMB domain/workgroup.")
@click.option("--temp-dir", "temp_dir", default=None, type=click.Path(), help="Override temp dir.")
@click.option("-v", "--verbose", is_flag=True, help="Show each file as extracted.")
def main(
    source: str,
    dest: str,
    dry_run: bool,
    no_skip_existing: bool,
    glob_filter: str | None,
    smb_username: str | None,
    smb_password: str | None,
    smb_domain: str | None,
    temp_dir: str | None,
    verbose: bool,
) -> None:
    """Set up an xStation SD card from game archives.

    SOURCE: Local directory path OR smb://[user:pass@]server/share[/path]

    DEST: Local path to SD card root
    """
    dest_path = Path(dest)
    temp_path = Path(temp_dir) if temp_dir else None
    skip_existing = not no_skip_existing

    if source.startswith("smb://"):
        _check_smb_available()
        if smb_password is None:
            smb_password = click.prompt("SMB password", hide_input=True, default="", show_default=False)

        from .sources.smb import SmbSource
        game_source = SmbSource(
            url=source,
            username=smb_username,
            password=smb_password,
            domain=smb_domain,
        )
        _check_rar_tool(None, is_smb=True)
    else:
        source_path = Path(source)
        if not source_path.is_dir():
            console.print(f"[red]Source directory not found:[/red] {source}")
            sys.exit(1)
        _check_rar_tool(source_path, is_smb=False)

        from .sources.local import LocalSource
        game_source = LocalSource(source_path, glob_filter=glob_filter)

    if not dry_run:
        dest_path.mkdir(parents=True, exist_ok=True)

    from .processor import process
    process(
        source=game_source,
        dest=dest_path,
        dry_run=dry_run,
        skip_existing=skip_existing,
        verbose=verbose,
        temp_dir=temp_path,
    )
