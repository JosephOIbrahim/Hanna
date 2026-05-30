# bin/ — Hanna launcher artifacts

What's here:

- `hanna-brief.command` — bash launcher that invokes `scripts/first_hanna_brief.py` end-to-end (composer + SQLite persistence + stdout). Tees output to `~/Library/Logs/hanna-brief.log` on macOS, `data/hanna-brief.log` on Linux dev.
- `com.hanna.brief.morning.plist` — launchd agent definition for the MORNING phase (Mon–Fri 09:00 local, per D010). One .plist per phase; this is the demonstration sibling.

## Install the launchd job (macOS)

```sh
# Substitute your $HOME path into the three /Users/YOUR_USERNAME/... slots
# inside the .plist before copying — launchd does not expand ~.
cp bin/com.hanna.brief.morning.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.hanna.brief.morning.plist
launchctl list | grep hanna
```

To unload: `launchctl unload ~/Library/LaunchAgents/com.hanna.brief.morning.plist`.

## Test the launcher manually

```sh
./bin/hanna-brief.command
```

Output prints to terminal and appends to the log file. Exit code propagates from the Python composer.

## Platform notes

Per D011, the calendar-channel and the launchd schedule are macOS-only. On Linux the bash launcher itself still runs (composer + persistence work); the .plist is inert without a launchd daemon to load it.
