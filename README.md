# gemini-autoclean

`gemini-autoclean` is a cross-platform helper around [`GeminiWatermarkTool`](https://github.com/allenk/GeminiWatermarkTool). It installs the watermark remover for the current OS, makes it callable globally, watches your Downloads folder, and automatically moves cleaned Gemini images into a dedicated `Gemini` folder.

## Features

- Auto-downloads the correct `GeminiWatermarkTool` build for Windows, Linux, or macOS
- Installs a global shim so `GeminiWatermarkTool` is callable from any terminal
- Watches the default Downloads folder by default
- Lets users override the source directory and target directory
- Matches files by configurable filename patterns such as `Gemini_Generated_Image_*`
- Removes the original file after a successful clean
- Installs autostart on Windows, Linux, and macOS

## Install

### Bootstrap script

Windows:

```powershell
.\install.ps1
```

Linux / macOS:

```bash
chmod +x ./install.sh
./install.sh
```

### pipx

```bash
pipx install .
gemini-autoclean setup
```

### pip

```bash
python -m pip install .
gemini-autoclean setup
```

## Quick start

```bash
gemini-autoclean setup
gemini-autoclean print-config
```

After `setup`, the watcher is configured for startup and also launched for the current session.

Default behavior:

- watch: your default Downloads directory
- clean target: `Downloads/Gemini`
- filename pattern: `Gemini_Generated_Image_*`

## Common commands

```bash
gemini-autoclean setup --source ~/Downloads --target ~/Downloads/Gemini
gemini-autoclean setup --pattern Gemini_Generated_Image_* --pattern My_Custom_Prefix_*
gemini-autoclean install-tool
gemini-autoclean install-service
gemini-autoclean update-config --pattern Another_Prefix_*
gemini-autoclean watch --once
gemini-autoclean print-config --json
```

## Configuration

Config path:

- Windows / Linux / macOS: `~/.gemini-autoclean/config.json`

Main fields:

- `source_dir`
- `target_dir`
- `patterns`
- `extensions`
- `poll_seconds`
- `settle_checks`
- `settle_delay_ms`
- `remove_original`
- `force_mode`
- `tool_path`
- `log_path`

## Autostart

- Windows: Startup folder VBS launcher
- Linux: user `systemd` service when available
- macOS: LaunchAgent plist

## Notes

- Filename matching is intentional. Matching files are processed directly.
- The default target folder is `Downloads/Gemini`.
- The watcher is designed for Gemini-style generated image filenames first; users can add more patterns if needed.
- This project automates a local tool. It does not use any external inference service.
