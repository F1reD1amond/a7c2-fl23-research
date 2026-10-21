# Windows desktop preview.10 validation

Final workflow simplification: 50 focused cases cover no cross-feature recovery gate, editable look operations after full readback, no separate look-verify control, automatic host profile binding and sound operations without a cold-recovery record. No new full-suite run was performed after that change; the earlier 334/20 run below is kept as historical coverage. Full verification is deferred until formal release as requested.

preview.10.7: 334 passed / 20 skipped across desktop, runtime and sound regressions, including real original-program compatibility tests. A separate offline reconstruction from the published v2 patch list reproduced the external `0x138832` failure before migration and passed afterward. Stock/old FL23/old FL23 with LUTs all produced complete six-look setup plans; native FL23 reapplication was idempotent and migration preserved unrelated LUT program bytes. Recovery UI tests cover 70% pending, 100% verified, failed verification retaining pending state, and mandatory restart/follow-up instructions. Startup notice and recovery dialogs were rendered. No physical camera operations were performed; recipient source bytes and original child state are absent from the supplied archives.

preview.10.6: 156 related cases passed, covering direct save without audition/confirmation/recovery, current converted bytes, missing-dependency failure before intent, fresh retry after host-only preparation and no replay of unknown native operations. The packaged EXE executed valid/missing/oversized boot CSV simulations, exact inverse and compiled five native workers using the owner's local program backup/3776-byte payload without USB. The owner's missing-module failure was retired from its empty native journal while preserving evidence and recovery confirmation. No physical persistent write/boot-audio acceptance occurred in this update.

preview.10.5: 151 related regressions passed. Coverage includes the powered-on audition dialog, distinct save prerequisites, exactly-once dialogs after worker exit, waiting rather than false installation completion, no automatic owner acceptance and installation after recorded confirmations. Two Qt dialogs were rendered/inspected. The packaged EXE returned `sound_cold_recovery_required / camera_io=false` from a copy of the owner's confirmed-but-not-recovered state without exceptions. Original sound records remain; no camera operation or physical persistent-install validation occurred in this update.

preview.10.4: 144 related regressions passed, adding pre-allocation EEXIST retirement, automatic replacement of an exact same-body completed marker, report/token matching, active-worker/unknown-result preservation and immutable old evidence. The owner's real report had phase 1/status -17 with no AP/CP/transfer calls. Its marker matched a historical completed registration. The packaged EXE archived/removed that marker on camera; normal audition will create a new one. No stale CP handle release, new registration or firmware write occurred. Listening remains pending.

preview.10.3: 129 related offline cases passed. New tests reproduced the exact missing-USB-field error before the fix and exercise the actual connector for legacy/fresh records, normal/service identities, re-enumeration, disconnects and non-replayed authentication errors. The packaged EXE's `sound_check_connection` successfully verified the owner's body and read AP/CP; the disk sound switch was OFF. No native worker, audio registration, program or settings write occurred. Physical playback remains untested in this update.

preview.10.2: 77 audio-related offline tests passed, covering release of completed read-only failures, fresh support adoption before audition, no permanent enable during audition, preservation of conversion/evidence, and continued blocking for unknown writes/registration/cleanup. The owner's actual failed job passed read-only classification without altering its files or operating the camera. Physical audition acceptance remains pending.

preview.10.1: 62 audio cases passed, including independent conversion with an unresolved camera task, fresh jobs, failure/cancellation cleanup and preservation of source/last successful output. The packaged EXE converted the owner’s actual source/parameters successfully (3776 bytes), with camera-task and source bytes unchanged; no camera I/O.

2026-10-21, ILCE-7CM2 / 2.01. Offline validation and physical acceptance are separate.

| Current checks | Result |
| --- | --- |
| Full desktop / vertical suite | 226 passed |
| Final GUI group, including preservation of unsent plans | 47 passed |
| Mixed operations / real-firmware planning | 29 passed, included in desktop total |
| Sound conversion / codec / CLI | 24 passed |
| Audio packaging regression | 3 passed, included in desktop total |

Overlapping groups are not summed. Prior preview.9.2 records remain: full LUT 235 passed / 16 skipped, FL23 84, runtime 26, sound/USB 91 passed / 7 skipped. Old native-preview emulation was not rerun for this update.

Coverage includes empty defaults, Restore as the new-item default, adjacent file/title controls, mixed writes/resets, duplicate targets, preservation of omitted slots/titles/recipes/calibration and FL23/sound, modern/legacy-six layouts, idempotent replanning, restored-slot RAW mappings after acceptance, and one backend transaction per batch.

Independent review found and fixed missing first-start import initialization and lost returned continuation workspaces. Regressions cover clean child interpreters, reopening pending tasks, locked reload plans, proven pre-write retry, unknown-write stopping, completion clearing, preserving unsent selections during old verification, and Home button labels.

The real frozen EXE imported generated WAV and stereo MP3 successfully (converted_offline, 2496 bytes, camera_io=false). Frozen self-test also converts mono WAV, stereo WAV and stereo MP3, checking native payloads and 24kHz previews to catch missing wave/ffmpeg dependencies. Seven-page and incremental-list screenshots check layout; ZIP validation checks member CRCs and updated contents.

No automated camera operations were performed. Mixed batches and this GUI still require owner-operated physical acceptance. Earlier preview.8 write/loaded-state evidence does not establish acceptance of every feature in this build; persisted Vertical Display, Fn/photo/video behavior and long-term stability remain separate checks.

[User guide](desktop.md) · [GUI regression](../../dev/desktop/test_look_editor.py) · [Mixed batches](../../dev/desktop/test_mixed_batch.py)
