# ČEZ Distribuce for Codex

English | [Česky](README.cs.md)

A community plugin for reading metered electricity consumption and grid export from the ČEZ Distribuce Metered Data Portal (PND).

It includes a repeatable export workflow using a signed-in Edge browser and local MCP tools for checking CSV files, generating daily summaries, and preserving original files with SHA256 verification. Neither the direct ČEZ API nor automatic sign-in is connected. The project is not officially affiliated with or endorsed by ČEZ Distribuce.

## Installation

For local Codex on Windows:

```powershell
codex plugin marketplace add petrkosekmb-commits/codex-plugin-cez-distribuce
codex plugin add cez-distribuce@cez-distribuce-community
```

After installation, open a new chat. Working with the portal requires a connected Edge browser-control integration and a valid PND login session. Local CSV processing requires Python 3.12; the launcher prefers the Codex runtime and otherwise uses Python from PATH. For timestamps with offsets, Python needs timezone data for Europe/Prague; on Windows, this can be provided by `tzdata`.

Example prompts: “Read the available electricity meters in ČEZ Distribuce”, “Download consumption and grid export for last month”, or “Check this CSV export and calculate daily totals”.

## Tools and configuration

- `cez_status`: status and availability of the local environment.
- `inspect_csv`: columns, encoding, delimiter, a small preview, and SHA256.
- `summarize_csv`: an explicitly selected series, units, filters, and statuses.
- `save_export`: preservation of the original file with copy verification.
- `list_exports`: a list of exports in the destination directories.

To configure your own primary storage location, set `CEZ_OUTPUT_DIR`; to configure the fallback directory, set `CEZ_PENDING_DIR`, both before starting Codex. The default paths are `Z:\ZALOHA\07_CODEX\outputs\cez-distribuce` and `%USERPROFILE%\Codex\pending-Z\outputs\cez-distribuce`. Use absolute paths outside OneDrive. The plugin does not synchronize the fallback directory itself and does not include a scheduler. The `z_verified` and `stored_on_z` flags refer to the primary storage location even when it has been reconfigured.

Details: [plugin guide](plugins/cez-distribuce/README.md), [portal workflow (Czech)](plugins/cez-distribuce/skills/cez-distribuce/references/portal.md), [API options (Czech)](plugins/cez-distribuce/skills/cez-distribuce/references/api.md).

## Verification status

Version 0.1.3 was tested on 8 October 2026 with a downloaded full CSV for one meter, profile +A/-A/Rv in kW, covering September 2026. All 2,880 quarter-hour intervals were present, and consumption and grid-export totals matched the portal statistics after rounding to three decimal places. One interval carried a measured-data voltage-outage status; it was explicitly included to reproduce the portal total. Real metered data are kept outside this repository.

The parser supports repeated `Datum`/`Status` headers using one-based column selectors (`#1`, `#2`, etc.), CP1250, decimal commas, and the PND end-of-day notation `24:00:00`. Select `timestamp_position="interval_end"` with the interval length to assign midnight readings to the previous day. Other export profiles, formats, and live daylight-saving-time exports have not been verified. Column mapping, quantity meaning, units, and acceptable statuses still require explicit selection; `cez_status` reports historical test scope, not current login or portal availability.

According to the [ČEZ terms](https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/sluzba-automatickeho-zasilani-namerenych-dat), the official AZD service requires separate activation and at least 30 supply points of type A/B. This version does not include a SOAP client.

## Development and privacy

```powershell
python -B -m unittest discover -s plugins/cez-distribuce/tests -v
```

The tests use synthetic CSV files and temporary directories. Do not store passwords, cookies, tokens, EAN identifiers, actual exports, or local configuration in the repository. Process metered data in your own storage location.

## Support the project

If you find the plugin helpful, you can support its continued development and maintenance on [Buy Me a Coffee](https://buymeacoffee.com/kojakcio). Thank you for your support.

## License

MIT. See [LICENSE](LICENSE).
