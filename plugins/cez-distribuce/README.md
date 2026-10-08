# ČEZ Distribuce — metered data

English | [Česky](README.cs.md)

A local plugin for Codex. It includes a workflow for reading and exporting data from a signed-in PND session in Edge, along with tools for checking, summarizing, and preserving CSV files. It contains no passwords or login session. The official AZD SOAP service is not connected.

A community project for Windows that is neither an official ČEZ Distribuce product nor endorsed by ČEZ Distribuce.

After installation, open a new chat and enter, for example: “Read the available electricity meters in ČEZ Distribuce” or “Download consumption and grid export for September 2026”. Downloading requires an available portal and a valid login session in Edge. No login is required to work with an already downloaded CSV file.

Version 0.1.3 was verified on 8 October 2026 using one actual full CSV export of +A/-A/Rv in kW for September 2026: 2,880 quarter-hour intervals, with energy totals matching the portal statistics to three decimal places. One interval marked as measured data with a voltage outage was explicitly included. This is a historical test of that format, not a check of the current session or all export profiles. No private metered data are included in the plugin.

Repeated column names are selected by one-based position, such as `timestamp_column="#1"`, `value_column="#2"`, and `status_column="#3"`, as listed by `inspect_csv`. For the verified full profile, the second series uses positions `#4`/`#5`/`#6`. Always check the current headers and units. Set `quantity="mean_power"`, `unit="kW"`, `interval_minutes=15`, `time_format="%d.%m.%Y %H:%M:%S"`, and `timestamp_position="interval_end"` only when this meaning is confirmed. PND midnight `24:00:00` becomes next-day `00:00:00`; the interval's energy belongs to the preceding day. Choose accepted statuses explicitly and report any outage or rejected data. Other formats and live daylight-saving-time exports remain unverified.

Tools: `cez_status`, `inspect_csv`, `summarize_csv`, `save_export`, `list_exports`. The CSV parser and stdio server use the Python 3.12 standard library. The launcher prefers Python from the local Codex runtime and otherwise looks for `python.exe` in PATH. The server can be started via `scripts/start-server.ps1`; the skill handles the portal separately through the connected browser. Timestamps with offsets require timezone data for Europe/Prague (on Windows, this can be provided by the `tzdata` package); `cez_status` reports its availability. Without it, conversion is refused.

By default, final exports are saved to `Z:\ZALOHA\07_CODEX\outputs\cez-distribuce`, or to `%USERPROFILE%\Codex\pending-Z\outputs\cez-distribuce` if the primary location is unavailable. To configure your own primary storage location, set the `CEZ_OUTPUT_DIR` environment variable, and set `CEZ_PENDING_DIR` for the fallback directory, before starting Codex. Specify absolute paths outside OneDrive. For compatibility, the output flag names `z_verified` and `stored_on_z` refer to the primary storage location even when it has been reconfigured. The copy is verified using SHA256. Existing files with different contents are not overwritten. The plugin does not synchronize the fallback directory itself.

Source for the API terms: https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/sluzba-automatickeho-zasilani-namerenych-dat

## Support the project

If you find the plugin helpful, you can support its continued development and maintenance on [Buy Me a Coffee](https://buymeacoffee.com/kojakcio). Thank you for your support.
