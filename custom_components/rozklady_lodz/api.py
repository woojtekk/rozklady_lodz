from __future__ import annotations

import re
from typing import Any, Dict
from xml.etree import ElementTree as ET

from aiohttp import ClientSession, ClientTimeout

NUM_RE = re.compile(r"\d+")


def _digits(value: str | None) -> int | None:
    if not value:
        return None
    match = NUM_RE.search(value)
    return int(match.group()) if match else None


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return _digits(value)


def _hhmm_to_minutes(hhmm: str) -> int | None:
    try:
        hours, minutes = hhmm.split(":")
        return int(hours) * 60 + int(minutes)
    except Exception:
        return None


class RozkladyAPI:
    """Async client for the rozklady.lodz.pl realtime endpoint."""

    def __init__(self, session: ClientSession, base_url: str) -> None:
        self._session = session
        self._base = base_url

    async def fetch_xml(self, stop_number: int, timeout: float = 10.0) -> bytes:
        params = {"busStopNum": str(stop_number)}
        headers = {"User-Agent": "HomeAssistant/rozklady_lodz (https://www.home-assistant.io/)"}
        timeout_cfg = ClientTimeout(total=timeout)
        async with self._session.get(
            self._base, params=params, headers=headers, timeout=timeout_cfg
        ) as response:
            response.raise_for_status()
            return await response.read()

    def parse(self, xml_bytes: bytes, only_trams: bool = True) -> Dict[str, Any]:
        root = ET.fromstring(xml_bytes)

        server_time = (root.attrib.get("time") or "").strip()
        server_minutes = _hhmm_to_minutes(server_time) if server_time else None

        stop = root.find(".//Stop")
        stop_name = stop.attrib.get("name", "") if stop is not None else ""

        result: Dict[str, Any] = {"stop_name": stop_name, "server_time": server_time, "departures": {}}

        for route in root.findall(".//R"):
            vehicle_type = (route.attrib.get("vt") or "").strip()
            if only_trams and vehicle_type and vehicle_type != "T":
                continue

            line = (route.attrib.get("nr") or "").strip()
            direction = (route.attrib.get("dir") or "").strip()

            items = []
            for sched in route.findall("./S"):
                th = (sched.attrib.get("th") or "").strip()
                tm = (sched.attrib.get("tm") or "").strip()
                t = (sched.attrib.get("t") or "").strip()
                m_attr = (sched.attrib.get("m") or "").strip()
                s_attr = (sched.attrib.get("s") or "").strip()

                minutes = None
                seconds_val = _to_int(s_attr)

                # Primary source: convert seconds (rounded up to the nearest full minute)
                if seconds_val is not None:
                    minutes = max(0, (seconds_val + 59) // 60)

                # Fallback #1: explicit minutes attribute
                if minutes is None:
                    minutes = _to_int(m_attr)

                # Fallback #2: absolute time minus current server time (mod 24 h)
                if minutes is None and server_minutes is not None and th and tm:
                    try:
                        departure_total = (int(th) * 60 + int(tm)) % (24 * 60)
                        minutes = (departure_total - server_minutes) % (24 * 60)
                    except Exception:
                        minutes = _digits(tm)

                # Fallback #3: digits inside the textual minutes representation
                if minutes is None:
                    minutes = _digits(tm)

                if th:
                    main_text = f"{th}:{tm.zfill(2) if tm else '00'}"
                else:
                    main_text = tm or (f"{minutes} min" if minutes is not None else "")
                pretty = f"{main_text} [t={t}, m={m_attr}]".strip()

                items.append(
                    {
                        "th": th,
                        "tm": tm,
                        "t": t,
                        "m": _to_int(m_attr),
                        "seconds": seconds_val,
                        "minutes": minutes,
                        "pretty": pretty,
                    }
                )

            items.sort(key=lambda item: (item["minutes"] is None, item["minutes"] or 10**9))

            if line not in result["departures"]:
                result["departures"][line] = {"dir": direction, "items": items}
            else:
                result["departures"][line]["items"].extend(items)
                if not result["departures"][line]["dir"] and direction:
                    result["departures"][line]["dir"] = direction

        return result
