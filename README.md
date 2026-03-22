# xstation-sd-util

CLI tool to set up an [xStation](https://castlemaniagames.com/products/xstation) (PS1 ODE mod chip) SD card from a library of game archives.

The xStation replaces the PS1 optical drive with a microSD card. Games are stored as folders containing disc images (`.bin`/`.cue`, `.iso`, `.ccd`/`.img`). For large libraries, games must be organized into alphabetical subfolders (`A`–`Z`, plus `#` for titles starting with numbers or symbols).

This tool reads game archives from a local directory or SMB share and extracts them into the correct SD card structure — automatically, in bulk.

## Features

- Extracts `.zip`, `.7z`, `.rar`, `.tar`, `.tar.gz` archives
- Automatically routes games into `A`–`Z` / `#` subfolders
- Skips already-extracted games by default (resumable)
- Re-extracts empty folders (recovers from interrupted runs)
- Atomic placement via temp dir + `os.rename()` — no partial game folders
- Dry-run mode to preview without writing anything
- Optional SMB source support (TrueNAS, Samba, etc.)

## Installation

```bash
git clone https://github.com/twoscomp/xstation-sd-util.git
cd xstation-sd-util
python3 -m venv --without-pip .venv
curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3
source .venv/bin/activate

pip install -e ".[dev]"          # local sources only
pip install -e ".[dev,smb]"      # include SMB support
```

**System dependency for RAR archives:** `unrar` or `bsdtar` must be installed.
```bash
# Debian/Ubuntu
sudo apt install unrar
# macOS
brew install rar
```

## Usage

```
xstation-sd-util [OPTIONS] SOURCE DEST

Arguments:
  SOURCE   Local directory path OR smb://[user:pass@]server/share[/path]
  DEST     Local path to SD card root

Options:
  -n, --dry-run              Show what would happen, don't extract
      --no-skip-existing     Re-extract even if folder exists
  -f, --filter GLOB          Only process archives matching pattern
      --smb-username TEXT    SMB username (overrides URL)
      --smb-password TEXT    SMB password (prompted if omitted)
      --smb-domain TEXT      SMB domain/workgroup
      --temp-dir PATH        Override temp dir (default: DEST/.xstation_tmp/)
  -v, --verbose              Show each file as extracted
```

### Examples

```bash
# Dry run from a local directory
xstation-sd-util --dry-run /mnt/nas/ps1_games /media/sdcard

# Extract all archives
xstation-sd-util /mnt/nas/ps1_games /media/sdcard

# SMB source (pass credentials as options to avoid shell quoting issues)
xstation-sd-util \
  --smb-username myuser \
  --smb-password 'mypassword' \
  'smb://truenas.local/media-all/games/PS1' \
  /media/sdcard
```

## Output Structure

```
/media/sdcard/
  00xstation/          ← system folder, never touched
  #/
    007 Racing/
      007 Racing.bin
      007 Racing.cue
  A/
    Ape Escape/
      Ape Escape.bin
      Ape Escape.cue
  B/
    ...
```

## Development

```bash
pytest tests/
```

## License

MIT
