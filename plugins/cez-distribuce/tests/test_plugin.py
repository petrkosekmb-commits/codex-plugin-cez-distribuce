import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cez", ROOT / "server.py")
cez = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cez)


class CSVTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.csv = self.root / "sample.csv"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, text, encoding="utf-8-sig"):
        self.csv.write_bytes(text.encode(encoding))
        return str(self.csv)

    def summary(self, **overrides):
        args = dict(path=str(self.csv), timestamp_column="Čas", value_column="Hodnota",
                    time_format="%d.%m.%Y %H:%M", quantity="interval_energy", unit="kWh")
        args.update(overrides)
        return cez.summarize_csv(**args)

    def test_czech_cp1250_and_decimal_comma(self):
        self.write('Čas;Hodnota;EAN\n01.09.2026 00:00;"1 234,50";001234\n01.09.2026 00:15;0,25;001234\n', "cp1250")
        inspected = cez.inspect_csv(path=str(self.csv))
        self.assertEqual(inspected["encoding"], "cp1250")
        self.assertEqual(inspected["preview"][0][2], "001234")
        self.assertEqual(self.summary()["total_kwh"], "1234.75")

    def test_mean_power_integrates_15_minutes(self):
        self.write("Čas;Hodnota\n01.09.2026 00:00;4\n01.09.2026 00:15;2\n")
        self.assertEqual(self.summary(quantity="mean_power", unit="kW", interval_minutes=15)["total_kwh"], "1.50")
        with self.assertRaises(ValueError):
            self.summary(quantity="mean_power", unit="kW")
        with self.assertRaises(ValueError):
            self.summary(unit="kW")

    def test_pnd_24_hour_endpoint_and_date_rollover(self):
        self.write("Čas;Hodnota\n30.09.2026 23:45:00;4\n30.09.2026 24:00:00;8\n01.10.2026 00:15:00;12\n")
        result = self.summary(time_format="%d.%m.%Y %H:%M:%S", quantity="mean_power",
                              unit="kW", interval_minutes=15, timestamp_position="interval_end")
        self.assertEqual(result["total_kwh"], "6.00")
        self.assertEqual(result["irregular_steps"], 0)
        self.assertEqual(result["daily"], [{"date": "2026-09-30", "kwh": "3.00"},
                                            {"date": "2026-10-01", "kwh": "3.00"}])
        self.assertEqual(cez.stamp("31.12.2026 24:00:00", "%d.%m.%Y %H:%M:%S").isoformat(),
                         "2027-01-01T00:00:00")
        for invalid in ("30.09.2026 24:01:00", "30.09.2026 24:00:01", "31.09.2026 24:00:00"):
            with self.assertRaises(ValueError):
                cez.stamp(invalid, "%d.%m.%Y %H:%M:%S")

    def test_register_difference_and_reset(self):
        self.write("Čas;Hodnota\n01.09.2026 00:00;100\n02.09.2026 00:00;104,5\n")
        self.assertEqual(self.summary(quantity="cumulative_register")["total_kwh"], "4.5")
        self.write("Čas;Hodnota\n01.09.2026 00:00;100\n02.09.2026 00:00;2\n")
        with self.assertRaises(ValueError):
            self.summary(quantity="cumulative_register")

    def test_missing_invalid_and_negative_are_not_zero(self):
        for value in ("", "NaN", "Infinity", "-1", "neznámo"):
            self.write(f"Čas;Hodnota\n01.09.2026 00:00;{value}\n")
            with self.assertRaises(ValueError):
                self.summary()

    def test_duplicate_timestamps_need_single_series_filter(self):
        self.write("Čas;Hodnota;EAN\n01.09.2026 00:00;1;001\n01.09.2026 00:00;3;002\n")
        with self.assertRaises(ValueError):
            self.summary()
        self.assertEqual(self.summary(filters={"EAN": "001"})["total_kwh"], "1")

    def test_dst_naive_repeated_and_nonexistent_times_rejected(self):
        for dt in ("25.10.2026 02:15", "29.03.2026 02:15"):
            self.write(f"Čas;Hodnota\n{dt};1\n")
            with self.assertRaises(ValueError):
                self.summary()

    def test_dst_distinct_offsets_remain_distinct(self):
        self.write("Čas;Hodnota\n2026-10-25T02:15:00+02:00;1\n2026-10-25T02:15:00+01:00;2\n")
        if cez.cez_status()["prague_timezone_available"]:
            result = self.summary(time_format="iso")
            self.assertEqual(result["samples"], 2)
            self.assertEqual(result["total_kwh"], "3")
            self.assertEqual(result["daily"][0]["date"], "2026-10-25")
        else:
            with self.assertRaises(ValueError):
                self.summary(time_format="iso")

    def test_preamble_requires_explicit_header_and_delimiter(self):
        self.write("Výpis PND\nČas;Hodnota\n01.09.2026 00:00;1\n")
        result = cez.inspect_csv(path=str(self.csv), header_row=2, delimiter=";")
        self.assertEqual(result["columns"], ["Čas", "Hodnota"])
        self.assertEqual(self.summary(header_row=2, delimiter=";")["total_kwh"], "1")

    def test_status_filter_reports_partial_sum(self):
        self.write("Čas;Hodnota;Stav\n01.09.2026 00:00;1;OK\n01.09.2026 00:15;2;ODHAD\n")
        with self.assertRaises(ValueError):
            self.summary(status_column="Stav")
        result = self.summary(status_column="Stav", accepted_statuses=["OK"])
        self.assertEqual(result["total_kwh"], "1")
        self.assertEqual(result["rejected_rows"], 1)
        self.assertIsNone(result["period_complete"])

    def test_pnd_repeated_headers_and_trailing_delimiter(self):
        self.write('Datum;+A/TEST [kW];Status;Datum;-A/TEST [kW];Status;\n01.09.2026 00:15:00;4;OK;01.09.2026 00:15:00;8;OK;\n01.09.2026 00:30:00;2;ODHAD;01.09.2026 00:30:00;4;OK;\n', 'cp1250')
        args = dict(path=str(self.csv), timestamp_column='#4', value_column='#5', time_format='%d.%m.%Y %H:%M:%S',
                    quantity='mean_power', unit='kW', interval_minutes=15, status_column='#6', accepted_statuses=['OK'])
        result = cez.summarize_csv(**args)
        self.assertEqual(result['total_kwh'], '3.00')
        self.assertEqual(result['selected_columns']['value']['position'], 5)
        with self.assertRaises(ValueError):
            cez.summarize_csv(**{**args, 'timestamp_column': 'Datum'})
        with self.assertRaises(ValueError):
            cez.summarize_csv(**{**args, 'value_column': '#99'})
        self.assertEqual(cez.inspect_csv(path=str(self.csv))['column_selectors'][3]['selector'], '#4')

    def test_interval_end_midnight_belongs_to_previous_day(self):
        self.write('Čas;Hodnota\n30.09.2026 23:45;4\n01.10.2026 00:00;8\n')
        result = self.summary(quantity='mean_power', unit='kW', interval_minutes=15, timestamp_position='interval_end')
        self.assertEqual(result['daily'], [{'date': '2026-09-30', 'kwh': '3.00'}])
        with self.assertRaises(ValueError):
            self.summary(timestamp_position='interval_end')

    def test_interval_crossing_midnight_without_boundary_refused(self):
        self.write('Čas;Hodnota\n01.10.2026 00:05;4\n')
        with self.assertRaises(ValueError):
            self.summary(quantity='mean_power', unit='kW', interval_minutes=15, timestamp_position='interval_end')

    def test_gaps_and_unsorted_data(self):
        self.write("Čas;Hodnota\n01.09.2026 00:30;2\n01.09.2026 00:00;1\n")
        result = self.summary(interval_minutes=15)
        self.assertEqual(result["irregular_steps"], 1)
        self.assertEqual(result["total_kwh"], "3")

    def test_html_login_page_rejected(self):
        self.write("<!DOCTYPE html><html>Login</html>")
        with self.assertRaises(ValueError):
            cez.inspect_csv(path=str(self.csv))

    def test_save_sha_fallback_and_no_overwrite(self):
        self.write("Čas;Hodnota\n01.09.2026 00:00;1\n")
        data = self.csv.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        zroot = self.root / "z/cez-distribuce"
        pending = self.root / "pending/cez-distribuce"
        with patch.object(cez, "Z_ROOT", zroot), patch.object(cez, "PENDING_ROOT", pending):
            result = cez.save_export(str(self.csv), "zari")
            self.assertFalse(result["z_verified"])
            self.assertEqual(result["sha256"], sha)
            zroot.parent.mkdir()
            onz = cez.save_export(str(self.csv), "zari")
            self.assertTrue(onz["z_verified"])
            target = Path(onz["path"])
            target.write_text("Odlišná existující data", encoding="utf-8")
            another = cez.save_export(str(self.csv), "zari")
            self.assertNotEqual(another["path"], str(target))
            self.assertEqual(target.read_text(encoding="utf-8"), "Odlišná existující data")
            with patch.object(cez, "save_to_root", side_effect=[OSError("síť"), {"z_verified": False}]):
                self.assertFalse(cez.save_export(str(self.csv), "zari")["z_verified"])
            self.assertEqual(len(cez.list_exports()["exports"]), 3)
        with self.assertRaises(ValueError):
            cez.save_export(str(self.csv), "../jiny")

    def test_empty_header_and_bad_shape(self):
        self.write("Čas;Hodnota;Hodnota\n01.09.2026 00:00;1;2\n")
        with self.assertRaises(ValueError):
            self.summary()
        self.write("Čas;Hodnota\n01.09.2026 00:00;1;2\n")
        with self.assertRaises(ValueError):
            self.summary(delimiter=";")


class MCPTests(unittest.TestCase):
    def test_protocol_and_invalid_arguments(self):
        init = cez.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-06-18")
        for args in ({"path": "x.csv", "header_row": 0}, {"path": "x.csv", "unknown": True}, {"path": 1}):
            response = cez.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "inspect_csv", "arguments": args}})
            self.assertTrue(response["result"]["isError"])
        self.assertIsNone(cez.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(cez.handle({"jsonrpc": "2.0", "id": 3, "method": "initialize", "params": "invalid"})["error"]["code"], -32602)

    def test_real_stdio_process_survives_bad_json(self):
        messages = ["bad-json", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
                    json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
                    json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "cez_status"}})]
        run = subprocess.run([sys.executable, "-B", "-u", str(ROOT / "server.py")], input="\n".join(messages) + "\n", capture_output=True, encoding="utf-8", timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        responses = [json.loads(x) for x in run.stdout.splitlines()]
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(len(responses[2]["result"]["tools"]), 5)
        status = json.loads(responses[3]["result"]["content"][0]["text"])
        self.assertFalse(status["direct_cez_api_connected"])

    @unittest.skipUnless(sys.platform == "win32", "Spouštěč Windows")
    def test_packaged_powershell_launcher(self):
        messages = [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
                    json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "cez_status"}})]
        run = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts/start-server.ps1")],
                             input="\n".join(messages) + "\n", capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(run.returncode, 0, run.stderr)
        responses = [json.loads(x) for x in run.stdout.splitlines()]
        self.assertEqual(len(responses), 2, run.stdout)
        self.assertEqual(responses[1]["id"], 2)


if __name__ == "__main__":
    unittest.main()
