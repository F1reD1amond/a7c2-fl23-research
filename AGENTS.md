# Repository entrypoint

The owner approved merging the physically verified LUT work into `main` on
October 19, 2026. Main now contains separate FL23 and LUT entries. Develop
future changes on feature branches and preserve existing release tags.
Read `docs/en/ai.md` before implementation.

- `src/fl23/`: exact-source FL2/FL3 installation, backup and verification.
- `src/looks/`: Independent DCP/LUT CLI, exact-source device jobs and offline research tools.
- `docs/en/` and `docs/zh-CN/`: matching English/Simplified Chinese guides.
- `docs/profiles/`: source inventory and original license text; original DCP bytes are Release assets.
- `FL23.cmd`: Windows GUI/device CLI for prepare/install/verify only.
- `lut.py`: portable import and single-slot restoration CLI; no GUI/CMD.
- `recovery.py`: independent full rollback from original FL23 backup2 or complete checkpoints; no LUT job dependency.

Follow `src/looks/AGENTS.md` for custom-look work. Run offline validation
before camera interaction. FL23 admits model/user-confirmed version 2.01
without a stock/repository firmware fingerprint whitelist, as requested by
the owner. New FL23 and checkpoint workers use edited-byte checks and full
host byte readback, without firmware SHA gates or repeated package SHA scans.
Keep actual patch-position conflict guards and body-bound backups. Existing
LUT import adapters retain their source fingerprints; single-slot restoration uses byte checks without firmware/backup/worker hash gates. Checkpoint rollback
is independent of their job order/output fingerprints.
Never repeat a write with an unknown outcome. Offline manifests alone are not an installation. The new
device importer passed two selected-slot updates on one Windows camera;
stock first-install, physical restoration and Mac USB remain untested.
Keep full firmware, body backups/calibration, photos and credentials private.
No Claude or additional agents without explicit user authorization.
