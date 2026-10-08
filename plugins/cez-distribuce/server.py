"""Local CSV tools; no network or credential access. JSON-RPC over stdio."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VERSION = "0.1.3"
PORTAL = "https://pnd.cezdistribuce.cz/cezpnd2/external/dashboard/view"
Z_ROOT = Path(os.environ.get("CEZ_OUTPUT_DIR", r"Z:\ZALOHA\07_CODEX\outputs\cez-distribuce")).expanduser()
PENDING_ROOT = Path(os.environ.get("CEZ_PENDING_DIR", str(Path.home() / "Codex/pending-Z/outputs/cez-distribuce"))).expanduser()
MAX_BYTES = 20 * 1024 * 1024


def source_file(path):
    p = Path(path).resolve(strict=True)
    if not p.is_file() or p.suffix.lower() not in (".csv", ".tsv"):
        raise ValueError("Zadejte místní soubor CSV nebo TSV.")
    # No output workflow should read the user's excluded OneDrive locations.
    if any(part.lower().startswith("onedrive") for part in p.parts):
        raise ValueError("Pro tento plugin přesuňte vybraný CSV mimo OneDrive.")
    if p.stat().st_size > MAX_BYTES:
        raise ValueError("Soubor přesahuje limit 20 MiB; rozdělte období exportu.")
    return p


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_csv(path, header_row=1, encoding=None, delimiter=None):
    p = source_file(path)
    data = p.read_bytes()
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Prázdný nebo příliš velký soubor.")
    if encoding is not None and encoding not in ("utf-8-sig", "utf-8", "cp1250"):
        raise ValueError("Podporované kódování: utf-8-sig, utf-8, cp1250.")
    for enc in ([encoding] if encoding else ["utf-8-sig", "cp1250"]):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Kódování CSV se nepodařilo rozpoznat.")
    if "\x00" in text or text.lstrip().lower().startswith(("<!doctype html", "<html")):
        raise ValueError("Soubor není textový CSV export; může jít o přihlašovací stránku.")
    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(text[:65536], delimiters=";\t,").delimiter
        except csv.Error:
            raise ValueError("Nelze určit oddělovač. Zadejte delimiter výslovně.") from None
    if delimiter not in (";", ",", "\t"):
        raise ValueError("Oddělovač musí být středník, čárka nebo tabulátor.")
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter, strict=True))
    if not 1 <= header_row <= len(rows):
        raise ValueError("header_row není platné pořadí záznamu CSV.")
    header = [v.strip().lstrip("\ufeff") for v in rows[header_row - 1]]
    return p, data, enc, delimiter, header, rows[header_row:], rows[:header_row - 1]


def inspect_csv(**args):
    p, data, enc, delim, header, rows, preamble = load_csv(**args)
    nonempty = [r for r in rows if any(v.strip() for v in r)]
    bad = [i + args.get("header_row", 1) + 1 for i, r in enumerate(rows)
           if any(v.strip() for v in r) and len(r) != len(header)]
    warnings = []
    if len(set(header)) != len(header) or any(not c for c in header):
        warnings.append("Hlavička obsahuje prázdné nebo duplicitní názvy; pro výpočet vyberte přesné pozice #1, #2… nebo opravte header_row.")
    if bad:
        warnings.append("Některé záznamy mají jiný počet polí než hlavička.")
    return {"path": str(p), "sha256": digest(data), "encoding": enc,
            "delimiter": delim, "columns": header, "data_rows": len(nonempty),
            "column_selectors": [{"selector": f"#{i}", "name": name} for i, name in enumerate(header, 1)],
            "preamble": preamble[:10], "preview": nonempty[:5],
            "inconsistent_rows": bad[:20], "warnings": warnings,
            "portal_schema_verified": False,
            "notice": "Rozpoznání CSV nepotvrzuje význam sloupců, jednotky ani úplnost období."}


def number(value):
    cleaned = value.strip().replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    if not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", cleaned):
        raise ValueError("Chybějící nebo neplatná číselná hodnota.")
    try:
        result = Decimal(cleaned.replace(",", "."))
    except InvalidOperation:
        raise ValueError("Neplatná číselná hodnota.") from None
    return result


def stamp(value, time_format):
    value = value.strip()
    # PND denotes midnight at the end of a day as dd.MM.yyyy 24:00:00.
    # Accept only that exact endpoint, never an invalid 24:01 or 24:00:01.
    if time_format == "%d.%m.%Y %H:%M:%S" and re.fullmatch(r"\d{2}\.\d{2}\.\d{4} 24:00:00", value):
        dt = datetime.strptime(value[:10], "%d.%m.%Y") + timedelta(days=1)
    else:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if time_format == "iso" else datetime.strptime(value, time_format)
    if dt.tzinfo is None and dt.month in (3, 10) and dt.hour == 2:
        # Czech repeated/nonexistent 02:xx on the last Sunday. Do not invent an offset.
        if dt.weekday() == 6 and dt.day + 7 > 31:
            raise ValueError("Čas ve dni změny času nemá offset a je nejednoznačný nebo neexistuje.")
    return dt


def column_index(selector, header):
    if isinstance(selector, str) and re.fullmatch(r"#[1-9]\d*", selector):
        index = int(selector[1:]) - 1
        if index >= len(header):
            raise ValueError("Pozice sloupce je mimo hlavičku CSV.")
        return index
    if not isinstance(selector, str) or not selector or header.count(selector) != 1:
        raise ValueError("Název sloupce chybí nebo není jednoznačný; použijte pozici #1, #2… od jedné.")
    return header.index(selector)


def summarize_csv(path, timestamp_column, value_column, time_format, quantity, unit,
                  header_row=1, encoding=None, delimiter=None, interval_minutes=None,
                  filters=None, status_column=None, accepted_statuses=None, timestamp_position="as_recorded"):
    p, data, enc, delim, header, rows, _ = load_csv(path, header_row, encoding, delimiter)
    filters = filters or {}
    time_index = column_index(timestamp_column, header)
    value_index = column_index(value_column, header)
    filter_indices = [(column_index(c, header), v) for c, v in filters.items()]
    status_index = None
    if status_column:
        status_index = column_index(status_column, header)
        if not accepted_statuses:
            raise ValueError("Pro status_column zadejte neprázdné accepted_statuses podle významu statusů PND.")
    elif accepted_statuses is not None:
        raise ValueError("accepted_statuses vyžaduje status_column.")
    factor = {"Wh": Decimal("0.001"), "kWh": Decimal(1), "MWh": Decimal(1000)}
    power = {"W": Decimal("0.001"), "kW": Decimal(1), "MW": Decimal(1000)}
    if quantity not in ("interval_energy", "mean_power", "cumulative_register"):
        raise ValueError("Neznámý význam veličiny.")
    if unit not in (power if quantity == "mean_power" else factor):
        raise ValueError("Jednotka neodpovídá významu veličiny.")
    minutes = None
    if interval_minutes is not None:
        minutes = Decimal(str(interval_minutes))
        if not minutes.is_finite() or not 0 < minutes <= 1440:
            raise ValueError("Délka intervalu musí být kladná a nejvýše 1440 minut.")
    if quantity == "mean_power" and minutes is None:
        raise ValueError("Průměrný výkon vyžaduje výslovnou délku měřeného intervalu.")
    if timestamp_position not in ("as_recorded", "interval_start", "interval_end"):
        raise ValueError("Neplatný význam časové značky.")
    if timestamp_position == "interval_end" and (minutes is None or quantity == "cumulative_register"):
        raise ValueError("Konec intervalu vyžaduje délku intervalu a intervalovou energii nebo průměrný výkon.")
    values = []
    rejected = []
    for i, row in enumerate(rows, header_row + 1):
        if not any(v.strip() for v in row):
            continue
        if len(row) != len(header):
            raise ValueError(f"Záznam {i} nemá stejný počet polí jako hlavička.")
        if any(row[c].strip() != v for c, v in filter_indices):
            continue
        if status_index is not None and row[status_index].strip() not in accepted_statuses:
            rejected.append(i)
            continue
        try:
            dt = stamp(row[time_index], time_format)
            val = number(row[value_index])
        except (ValueError, OverflowError):
            raise ValueError(f"Záznam {i}: neplatná hodnota nebo čas. Chybějící hodnota se nenahrazuje nulou; změna času vyžaduje offset.") from None
        if val < 0:
            raise ValueError(f"Záznam {i}: záporná hodnota vyžaduje samostatné ověření znaménkové konvence.")
        values.append((dt, val))
    if not values:
        raise ValueError("Pro zvolené sloupce, filtry a statusy nejsou data.")
    if len({dt.tzinfo is not None for dt, _ in values}) > 1:
        raise ValueError("Soubor míchá časy s offsetem a bez offsetu.")
    aware = values[0][0].tzinfo is not None
    zone = None
    if aware:
        try:
            zone = ZoneInfo("Europe/Prague")
        except ZoneInfoNotFoundError:
            raise ValueError("Runtime nemá databázi Europe/Prague; denní převod nelze bezpečně provést.") from None
    key = lambda dt: dt.astimezone(timezone.utc) if aware else dt
    keys = [key(dt) for dt, _ in values]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicitní čas v jedné sérii: ověřte filtr elektroměru/profilu a offset při změně času.")
    values.sort(key=lambda x: key(x[0]))
    gaps = None
    if minutes is not None:
        expected = minutes * 60
        gaps = sum(Decimal(str((key(b[0]) - key(a[0])).total_seconds())) != expected
                   for a, b in zip(values, values[1:]))
    warnings = ["Úplnost požadovaného období nebyla potvrzena; ověřte krajní časy a počet intervalů."]
    if not aware:
        warnings.append("Časy bez offsetu jsou ponechány v místním čase; rozdíly kolem změny času mohou být zdánlivé.")
    if rejected:
        warnings.append("Část řádků vyloučena podle statusu; součet není celá série.")
    if gaps:
        warnings.append("Časové rozestupy neodpovídají zadanému intervalu; ověřte chybějící data.")
    base = {"path": str(p), "sha256": digest(data), "samples": len(values),
            "quantity": quantity, "input_unit": unit, "output_unit": "kWh",
            "first_timestamp": values[0][0].isoformat(), "last_timestamp": values[-1][0].isoformat(),
            "accepted_statuses": accepted_statuses, "rejected_rows": len(rejected),
            "rejected_row_examples": rejected[:20], "irregular_steps": gaps,
            "filters": filters, "daily_timezone": "Europe/Prague" if aware else "místní časy CSV bez offsetu",
            "period_complete": None, "warnings": warnings}
    base["selected_columns"] = {"timestamp": {"selector": timestamp_column, "position": time_index + 1, "name": header[time_index]},
                                "value": {"selector": value_column, "position": value_index + 1, "name": header[value_index]}}
    base["timestamp_position"] = timestamp_position
    if quantity == "cumulative_register":
        if len(values) < 2 or any(b[1] < a[1] for a, b in zip(values, values[1:])):
            raise ValueError("Registr vyžaduje nejméně dvě hodnoty bez poklesu/resetu.")
        base.update({"total_kwh": str((values[-1][1] - values[0][1]) * factor[unit]),
                     "daily": None, "notice": "Rozdíl registru mezi první a poslední časovou značkou; nejde o součet intervalů."})
        return base
    multiplier = power[unit] * minutes / 60 if quantity == "mean_power" else factor[unit]
    daily = defaultdict(Decimal)
    for dt, val in values:
        at = key(dt) if aware else dt
        if timestamp_position == "interval_end":
            interval_start = at - timedelta(minutes=float(minutes))
            just_before_end = at - timedelta(microseconds=1)
            start_day = (interval_start.astimezone(zone) if aware else interval_start).date()
            end_day = (just_before_end.astimezone(zone) if aware else just_before_end).date()
            if start_day != end_day:
                raise ValueError("Interval zasahuje do více místních dnů; denní energii nelze bez rozdělení určit.")
            at = just_before_end
        day = (at.astimezone(zone) if aware else at).date().isoformat()
        daily[day] += val * multiplier
    base.update({"total_kwh": str(sum(daily.values(), Decimal(0))),
                 "daily": [{"date": day, "kwh": str(val)} for day, val in sorted(daily.items())],
                 "daily_attribution": "Energie patří dni intervalu před koncovou značkou, včetně půlnoci předchozího dne." if timestamp_position == "interval_end" else "Energie je přiřazena datu časové značky CSV; ověřte, zda jde o začátek nebo konec intervalu."})
    return base


def save_to_root(p, data, label, root, z_verified):
    root.mkdir(parents=True, exist_ok=True)
    sha = digest(data)
    target = root / f"{label}-{sha[:12]}{p.suffix.lower()}"
    if target.exists() and digest(target.read_bytes()) != sha:
        target = root / f"{label}-{sha}{p.suffix.lower()}"
    try:
        with target.open("xb") as f:
            f.write(data)
    except FileExistsError:
        pass
    if digest(target.read_bytes()) != sha:
        raise OSError("Cílový soubor neodpovídá originálu; kopie není ověřena.")
    return {"path": str(target), "sha256": sha, "bytes": len(data),
            "copy_verified": True, "z_verified": z_verified,
            "notice": "Kopie v hlavním cílovém úložišti ověřena." if z_verified else "Soubor v záložní složce; kopie v hlavním úložišti dosud není ověřena."}


def save_export(path, label):
    p = source_file(path)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", label):
        raise ValueError("label: 1 až 80 znaků latinky bez diakritiky, číslic, podtržítka nebo pomlčky.")
    data = p.read_bytes()
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Prázdný nebo příliš velký soubor.")
    if Z_ROOT.parent.is_dir():
        try:
            return save_to_root(p, data, label, Z_ROOT, True)
        except OSError:
            pass
    return save_to_root(p, data, label, PENDING_ROOT, False)


def list_exports():
    files = []
    for root, z_verified in ((Z_ROOT, True), (PENDING_ROOT, False)):
        try:
            for p in root.iterdir():
                if p.is_file() and p.suffix.lower() in (".csv", ".tsv"):
                    files.append({"path": str(p), "bytes": p.stat().st_size,
                                  "modified": p.stat().st_mtime, "stored_on_z": z_verified})
        except FileNotFoundError:
            continue
        except OSError:
            continue
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"exports": files[:100], "truncated": len(files) > 100,
            "notice": "stored_on_z označuje umístění v hlavním úložišti CEZ_OUTPUT_DIR, nikoli nové ověření SHA256."}


def cez_status():
    try:
        ZoneInfo("Europe/Prague")
        tz_available = True
    except ZoneInfoNotFoundError:
        tz_available = False
    return {"version": VERSION, "portal_url": PORTAL, "mode": "portal_browser_and_local_csv",
            "direct_cez_api_connected": False, "credentials_stored": False,
            "live_export_verified": True, "schema_verified": True,
            "verification": {"tested_on": "2026-10-08", "scope": "Jeden úplný CSV export profilu +A/-A/Rv v kW za září 2026, 2880 patnáctiminutových intervalů; součty porovnány se statistikou PND.",
                             "current_session_checked": False, "all_export_formats_verified": False},
            "prague_timezone_available": tz_available,
            "z_available": Z_ROOT.parent.is_dir(), "final_root": str(Z_ROOT),
            "pending_root": str(PENDING_ROOT),
            "notice": "Historické ověření exportu proběhlo 8. 10. 2026 v uvedeném rozsahu; nejde o kontrolu aktuální dostupnosti portálu. Místní nástroje nečtou živou relaci prohlížeče."}


def schema(properties=None, required=None):
    result = {"type": "object", "properties": properties or {}, "additionalProperties": False}
    if required:
        result["required"] = required
    return result


TEXT = {"type": "string", "minLength": 1}
CSV_ARGS = {"path": TEXT, "header_row": {"type": "integer", "minimum": 1},
            "encoding": {"type": "string", "enum": ["utf-8-sig", "utf-8", "cp1250"]},
            "delimiter": {"type": "string", "enum": [";", ",", "\t"]}}
SUMMARY_ARGS = {**CSV_ARGS, "timestamp_column": TEXT, "value_column": TEXT,
                "time_format": TEXT,
                "quantity": {"type": "string", "enum": ["interval_energy", "mean_power", "cumulative_register"]},
                "unit": {"type": "string", "enum": ["Wh", "kWh", "MWh", "W", "kW", "MW"]},
                "interval_minutes": {"type": "number", "exclusiveMinimum": 0, "maximum": 1440},
                "filters": {"type": "object", "additionalProperties": {"type": "string"}},
                "status_column": TEXT,
                "timestamp_position": {"type": "string", "enum": ["as_recorded", "interval_start", "interval_end"]},
                "accepted_statuses": {"type": "array", "minItems": 1, "items": {"type": "string"}}}
TOOLS = [
    ("cez_status", "Stav místního pluginu a pravdivé rozlišení portálu a nepřipojeného API ČEZ.", schema(), True, cez_status),
    ("inspect_csv", "Prohlédne místní CSV/TSV a vrátí sloupce, nejvýše 5 řádků a SHA256. Neověřuje význam dat ČEZ.", schema(CSV_ARGS, ["path"]), True, inspect_csv),
    ("summarize_csv", "Spočítá explicitně zvolenou sérii CSV. Vyžaduje význam veličiny, jednotku a čas; neúplnost ani statusy neodhaduje.", schema(SUMMARY_ARGS, ["path", "timestamp_column", "value_column", "time_format", "quantity", "unit"]), True, summarize_csv),
    ("save_export", "Uchová místní originální CSV v určeném úložišti Z nebo pending-Z a ověří SHA256; nepřepisuje odlišné soubory.", schema({"path": TEXT, "label": TEXT}, ["path", "label"]), False, save_export),
    ("list_exports", "Seznam nejvýše 100 místních exportů pluginu; neskenuje jiné složky NAS.", schema(), True, list_exports),
]


def validate_arguments(args, definition):
    if not isinstance(args, dict) or set(args) - set(definition["properties"]):
        raise ValueError("Neznámý nebo neplatný argument nástroje.")
    if any(k not in args for k in definition.get("required", [])):
        raise ValueError("Chybí povinný argument nástroje.")
    for k, value in args.items():
        prop = definition["properties"][k]
        typ = prop["type"]
        correct = {"string": isinstance(value, str), "integer": type(value) is int,
                   "number": type(value) in (int, float), "object": isinstance(value, dict),
                   "array": isinstance(value, list)}[typ]
        if not correct or ("enum" in prop and value not in prop["enum"]):
            raise ValueError(f"Neplatný argument {k}.")
        if typ == "string" and len(value) < prop.get("minLength", 0):
            raise ValueError(f"Prázdný argument {k}.")
        if typ in ("integer", "number"):
            if not Decimal(str(value)).is_finite():
                raise ValueError(f"Argument {k} musí být konečné číslo.")
            if value < prop.get("minimum", float("-inf")) or value > prop.get("maximum", float("inf")) or value <= prop.get("exclusiveMinimum", float("-inf")):
                raise ValueError(f"Argument {k} je mimo povolený rozsah.")
        if typ == "object" and any(not isinstance(v, str) for v in value.values()):
            raise ValueError("Hodnoty filtrů musí být text.")
        if typ == "array" and (len(value) < prop.get("minItems", 0) or any(not isinstance(v, str) for v in value)):
            raise ValueError("Statusy musí být neprázdný seznam textových hodnot.")


def handle(message):
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Neplatná zpráva."}}
    if "id" not in message:
        return None
    reqid = message["id"]
    method = message.get("method")
    if message.get("params") is not None and not isinstance(message["params"], dict):
        return {"jsonrpc": "2.0", "id": reqid, "error": {"code": -32602, "message": "Parametry musí být objekt."}}
    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion", "2024-11-05")
        supported = requested if requested in ("2024-11-05", "2025-03-26", "2025-06-18") else "2024-11-05"
        result = {"protocolVersion": supported, "capabilities": {"tools": {}},
                  "serverInfo": {"name": "cez-distribuce", "version": VERSION}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [{"name": n, "description": d, "inputSchema": s,
                              "annotations": {"readOnlyHint": ro, "destructiveHint": False, "openWorldHint": False}}
                             for n, d, s, ro, _ in TOOLS]}
    elif method == "tools/call":
        params = message.get("params") or {}
        try:
            matched = next((t for t in TOOLS if t[0] == params.get("name")), None)
            if matched is None:
                raise ValueError("Neznámý nástroj.")
            args = params.get("arguments", {})
            validate_arguments(args, matched[2])
            out = matched[4](**args)
            result = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}]}
        except (ValueError, OSError, csv.Error, TypeError, OverflowError) as exc:
            result = {"isError": True, "content": [{"type": "text", "text": str(exc)}]}
    else:
        return {"jsonrpc": "2.0", "id": reqid, "error": {"code": -32601, "message": "Neznámá metoda."}}
    return {"jsonrpc": "2.0", "id": reqid, "result": result}


def main():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        try:
            result = handle(json.loads(line))
        except json.JSONDecodeError:
            result = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Neplatný JSON."}}
        if result is not None:
            print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
