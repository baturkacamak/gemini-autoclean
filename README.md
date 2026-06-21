# gemini-autoclean

`gemini-autoclean` installs `GeminiWatermarkTool`, makes it reachable from the user environment, watches the default Downloads directory, and automatically moves cleaned Gemini images into a dedicated folder.

## What it does

- Detects the current platform and downloads the correct `GeminiWatermarkTool` release
- Installs the tool into a user-owned directory
- Creates a global shim so `GeminiWatermarkTool` can be called directly
- Watches the default Downloads folder or a user-specified directory
- Matches files by filename patterns such as `Gemini_Generated_Image_*`
- Cleans matching files and moves the cleaned result into a target folder
- Removes the original file after a successful clean
- Installs autostart on Windows, Linux, and macOS

## Install

### With `pipx` (recommended)

```bash
pipx install .
gemini-autoclean setup
```

### With `pip`

```bash
python -m pip install .
gemini-autoclean setup
```

### With bootstrap scripts

Windows:

```powershell
.\install.ps1
```

Linux / macOS:

```bash
./install.sh
```

## Basic usage

```bash
gemini-autoclean setup
gemini-autoclean watch
gemini-autoclean print-config
```

## Useful commands

```bash
gemini-autoclean setup --source ~/Downloads --pattern Gemini_Generated_Image_* --pattern My_Custom_Prefix_*
gemini-autoclean install-tool
gemini-autoclean install-service
gemini-autoclean update-config --pattern Another_Prefix_*
gemini-autoclean watch --once
```

## Configuration

The config file is stored in:

- Windows / Linux / macOS: `~/.gemini-autoclean/config.json`

Main options:

- `source_dir`
- `target_dir`
- `patterns`
- `extensions`
- `poll_seconds`
- `remove_original`
- `force_mode`
- `tool_path`

## Notes

- Filename matching is intentional. Files matching the configured patterns are processed directly.
- The default cleaned folder is `Downloads/Gemini`.
- On Linux, autostart uses a user `systemd` service when available.
- On macOS, autostart uses a LaunchAgent.
