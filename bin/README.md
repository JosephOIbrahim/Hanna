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

## Data retention

The `briefs` table in `data/hanna.sqlite` is append-only by design. D012 idempotency (the `brief_id` UNIQUE index, INSERT OR IGNORE) prevents duplicate rows from re-runs within the same phase window, so the table grows at most one row per scheduled phase fire.

Expected volume: ~10 briefs/week × ~2KB body ≈ ~1MB/year. No active retention is configured; the corpus is small enough that the first five years fit comfortably in a single SQLite file.

Future retention hook (catalogued for L6+, not implemented): a `python3 -m src vacuum --keep-days N` subcommand could DELETE briefs older than N days and then VACUUM. Surfaced here so the path is named; the actual implementation lives behind an explicit Joe ratification later.

Backup posture: `data/hanna.sqlite` is gitignored. Backup belongs to whichever macOS layer Joe already trusts — iCloud Drive sync on the data directory, or Time Machine on `$HOME`. Hanna does not manage backup rotation itself.

No SQLite encryption / TDE. The corpus is brief bodies, ISO timestamps, and dedup keys derived from product names — no secrets, no PII beyond the producer's own surfaced observations.
