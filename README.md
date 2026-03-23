# xstation-sd-util

CLI tool to set up an [xStation](https://castlemaniagames.com/products/xstation) (PS1 ODE mod chip) SD card from a library of game archives.

The xStation replaces the PS1 optical drive with a microSD card. Games are stored as folders containing disc images (`.bin`/`.cue`, `.iso`, `.ccd`/`.img`). For large libraries, games must be organized into alphabetical subfolders (`A`–`Z`, plus `#` for titles starting with numbers or symbols).

This tool automates both jobs: setting up the SD card system folder and extracting a full game library into the correct structure — in bulk, from a local directory or SMB share.

## Features

- **`extract`** — bulk-extract game archives onto an SD card
  - Supports `.zip`, `.7z`, `.rar`, `.tar`, `.tar.gz`
  - Automatically routes games into `A`–`Z` / `#` subfolders
  - Skips already-extracted games by default (resumable)
  - Per-game progress counter `[N/total]` and failure summary
  - Atomic placement via temp dir + `os.rename()` — no partial game folders
  - Dry-run mode to preview without writing anything
  - Optional SMB source support (TrueNAS, Samba, etc.)
- **`setup`** — prepare the SD card system folder and install firmware
  - Creates the `00xstation/` system directory
  - Downloads latest firmware from GitHub or installs from a local file/zip
  - Optional `--format DEVICE` to format the card with the SD Association formatter before setup

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
# Debian/Ubuntu/Fedora
sudo apt install unrar        # or: sudo dnf install unar
# macOS
brew install rar
```

**Optional: faster `.7z` extraction.** `py7zr` is used by default; installing the system `7z` binary improves compatibility with some archives.
```bash
# Fedora/Bazzite
sudo dnf install p7zip p7zip-plugins
# Debian/Ubuntu
sudo apt install 7zip
```

## Usage

### extract

Extract game archives onto an SD card.

```
xstation-sd-util extract [OPTIONS] SOURCE DEST

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
  -y, --yes                  Skip confirmation prompt
```

```bash
# Dry run from a local directory
xstation-sd-util extract --dry-run /mnt/nas/ps1_games /run/media/user/sdcard

# Extract all archives
xstation-sd-util extract /mnt/nas/ps1_games /run/media/user/sdcard

# SMB source (pass credentials as options to avoid shell-quoting issues)
xstation-sd-util extract \
  --smb-username myuser \
  --smb-password 'mypassword' \
  'smb://truenas.local/media-all/games/PS1' \
  /run/media/user/sdcard
```

### setup

Create the `00xstation/` system directory and install firmware on an already-mounted SD card.

```
xstation-sd-util setup [OPTIONS] MOUNTPOINT

Arguments:
  MOUNTPOINT   Path to the mounted SD card root

Options:
      --format DEVICE    Block device to format before setup (e.g. /dev/sdc).
                         Requires root. Uses the SD Association formatter (format_sd).
      --label TEXT       FAT32 volume label — only used with --format  [default: xstation]
      --firmware PATH    Local firmware directory or .zip to install
      --skip-firmware    Skip firmware installation
  -y, --yes              Skip confirmation prompt (only used with --format)
  -n, --dry-run          Show what would happen, don't modify anything
```

```bash
# Set up an already-mounted card and download the latest firmware
xstation-sd-util setup /run/media/user/sdcard

# Install firmware from a local zip
xstation-sd-util setup /run/media/user/sdcard --firmware ~/Downloads/update220.zip

# Format, then set up (requires root; format_sd binary must be in bin/)
sudo xstation-sd-util setup /run/media/user/sdcard --format /dev/sdc
```

**`--format` requires the SD Association formatter binary.** Download from [sdcard.org](https://www.sdcard.org/downloads/formatter/sd-memory-card-formatter-for-linux/) and place it at `bin/format_sd` in the project directory.

## Output Structure

```
/run/media/user/sdcard/
  00xstation/          ← system folder (firmware lives here)
    update.bin
    loader.bin
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
