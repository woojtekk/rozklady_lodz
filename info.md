## Rozklady Lodz

Realtime departures for Łódź directly in Home Assistant. Each configured line becomes its own sensor that shows the minutes to the next departure and exposes the raw timetable entries as attributes.

### Highlights
- Config flow that validates the stop number against rozklady.lodz.pl.
- Tram-only mode plus configurable poll interval (30–600 s).
- English and Polish translations.

### Installation
1. Add `https://github.com/woojtekk/rozklady_lodz` to HACS as a custom integration repository.
2. Install **Rozklady Lodz** from HACS and restart Home Assistant.
3. Add the integration from Settings → Devices & Services.

See the repository README for manual install instructions and release packaging tips.
