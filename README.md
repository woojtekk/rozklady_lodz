# Rozklady Lodz

Custom Home Assistant integration that exposes realtime departure data from [rozklady.lodz.pl](http://rozklady.lodz.pl) as minute-based sensors. Each configured line becomes a dedicated sensor whose state represents minutes to the next departure and attributes list the upcoming departures.

## Features
- Config flow with validation against the live API
- Separate sensors per line with minute estimates, pretty-formatted schedules, direction reminders, and stop metadata
- Options flow for refresh interval, tracked lines, and tram-only filtering
- Localised strings in English and Polish

## Requirements
- Home Assistant 2024.1.0 or newer (matches `manifest.json`)
- Internet access from Home Assistant to `rozklady.lodz.pl`

## Installation

### Via HACS (recommended)
1. In HACS → Integrations → ⋮ → **Custom repositories**, add `https://github.com/woojtekk/rozklady_lodz` as **Integration**.
2. Find **Rozklady Lodz** in the custom section and install it.
3. Restart Home Assistant when prompted.

### Manual copy
1. Download the latest release archive (see Releases tab) or clone the repository.
2. Copy the `custom_components/rozklady_lodz` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration
1. Settings → Devices & Services → **Add Integration** → search for *Rozklady Lodz*.
2. Enter the stop number (`busStopNum` from rozklady.lodz.pl), comma-separated line numbers, and optionally change the entity name prefix.
3. After setup you can open the integration options to:
   - Update the set of tracked line numbers.
   - Change the refresh interval (30–600 seconds).
   - Toggle the *Trams only* filter (defaults to enabled).

Sensors expose extra attributes such as the pretty timetable entries, stop name, direction, and the raw list of minutes for quick templating.

## Releases and HACS packaging
The repository already contains `hacs.json` that instructs HACS to download `rozkladylodz.zip`. Every time you publish a release:
1. Bump the `version` in `custom_components/rozklady_lodz/manifest.json`.
2. Zip the `custom_components/rozklady_lodz` folder only and name it `rozkladylodz.zip`.
3. Attach that zip to the GitHub release that matches the tag (e.g. `v0.2.1`).

Keeping `zip_release` set to `true` means HACS will prefer the packaged archive, so make sure it always mirrors the repository contents. Add release notes to `info.md` (see below) if you want custom text inside HACS.

## Development
- `hacs.json` governs how HACS interprets the repository.
- `info.md` (next to this README) is what HACS renders in its details panel.
- `.gitignore` excludes caches/virtual-env artefacts to keep releases clean.

Issues and pull requests are welcome in the GitHub repository.
