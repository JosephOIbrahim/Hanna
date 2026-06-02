# bin/ — Hanna launcher artifacts

What's here:

- `hanna-brief.command` — bash launcher that invokes `scripts/first_hanna_brief.py` end-to-end (composer + SQLite persistence + stdout). Tees output to `~/Library/Logs/hanna-brief.log` on macOS, `data/hanna-brief.log` on Linux dev.
- `com.hanna.brief.morning.plist` — launchd agent definition for the MORNING phase (Mon–Fri 09:00 local, per D010).
- `com.hanna.brief.midday.plist` — MIDDAY phase (Mon–Fri 12:00 local).
- `com.hanna.brief.evening.plist` — EVENING phase (Mon–Fri 17:00 local).
- `com.hanna.brief.weekly_monday.plist` — WEEKLY_MONDAY phase (Mon 09:30 local).
- `com.hanna.brief.weekly_friday.plist` — WEEKLY_FRIDAY phase (Fri 16:00 local).

Per D010 each phase has its own anchor; one .plist per phase keeps the launchd schedule explicit and editable per phase without affecting the others.

## Calendar.app permission grant (one-time, macOS)

Hanna's `src/channels/calendar.py` calls `osascript` to author events on Calendar.app via AppleScript. macOS requires explicit Automation permission for that surface; the first publish triggers a system prompt, but launchd jobs run headless and never see the prompt — they fail with AppleScript error `-1743` until permission is granted.

Grant once via:

1. Open **System Settings → Privacy & Security → Automation**.
2. Find **Terminal.app** (or the Python binary `python3` if launching from a different shell) and grant it access to **Calendar.app**.
3. If the launchd job already failed, unload + reload the .plist after granting:

   ```sh
   launchctl unload ~/Library/LaunchAgents/com.hanna.brief.morning.plist
   launchctl load ~/Library/LaunchAgents/com.hanna.brief.morning.plist
   ```

`HannaCalendarPermissionRequired` is the exception class surfacing this state; the message names the System Settings path.

## Required iCloud calendars (one-time, manual)

Per D006, Hanna publishes to a **dedicated** `Hanna` iCloud calendar and archives completed briefs to `Hanna · Archive`. Hanna **does not auto-create** these calendars — Joe creates them so the channel respects his calendar set:

1. Open **Calendar.app**.
2. **File → New Calendar → iCloud**, name it `Hanna`. (Optional: assign a calm color; D006's posture is "context the day carries.")
3. **File → New Calendar → iCloud**, name it `Hanna · Archive`. (Includes the U+00B7 middle dot — copy from this README if needed.)

If `Hanna · Archive` is missing, `archive(event_id)` raises `HannaCalendarNotFound` cleanly; nothing is silently dropped. If a calendar named `Hanna` is missing, the first `publish()` call surfaces an AppleScript failure rather than authoring a stray one.

## Install the launchd jobs (macOS)

```sh
# Substitute your $HOME path into the three /Users/YOUR_USERNAME/... slots
# inside each .plist before copying — launchd does not expand ~.
cp bin/com.hanna.brief.morning.plist ~/Library/LaunchAgents/
cp bin/com.hanna.brief.midday.plist ~/Library/LaunchAgents/
cp bin/com.hanna.brief.evening.plist ~/Library/LaunchAgents/
cp bin/com.hanna.brief.weekly_monday.plist ~/Library/LaunchAgents/
cp bin/com.hanna.brief.weekly_friday.plist ~/Library/LaunchAgents/

launchctl load ~/Library/LaunchAgents/com.hanna.brief.morning.plist
launchctl load ~/Library/LaunchAgents/com.hanna.brief.midday.plist
launchctl load ~/Library/LaunchAgents/com.hanna.brief.evening.plist
launchctl load ~/Library/LaunchAgents/com.hanna.brief.weekly_monday.plist
launchctl load ~/Library/LaunchAgents/com.hanna.brief.weekly_friday.plist

launchctl list | grep hanna
```

To unload any job: `launchctl unload ~/Library/LaunchAgents/com.hanna.brief.<phase>.plist`.

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
