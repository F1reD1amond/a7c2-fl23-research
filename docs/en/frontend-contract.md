# Backend contract for frontend replacement

This documents existing action names, arguments, results and logs. Windows and macOS call the same feature engines; the backend handles host authorization.

## Boundaries

- `window.py` / `lookeditor.py`: presentation and user input.
- `jobs.py`: job creation, worker command and diagnostics export.
- `actions/catalog.py`: the single camera/power action classification; `jobs.py` re-exports the same objects.
- `actions/look_compiler.py` / `actions/sound.py`: standalone compiler and shared sound adapters.
- `worker.py`: shared dispatch and complete process/error logging.
- `allinone.py`: coordinated installation, using `looktool.direct` for planning/writes.
- `platforms/`: host driver/media handling and macOS Terminal authorization.

Create work with `jobs.new_job(action, arguments)` and launch `jobs.worker_command(job / 'request.private.json')`. The UI thread does not call camera, driver or native-worker functions directly.

Requests keep `schema`, `action`, `arguments`, `job_dir` and `version`. The schema is `a7c2-desktop-job/1`. `status.private.json` uses `QUEUED`, `WAITING_AUTHORIZATION`, `RUNNING`, `SUCCEEDED` or `FAILED`. A successful worker contains `result`; failures retain `error`, `error_type` and the complete `worker.log` traceback.

`SUCCEEDED` means that worker action returned, not that the entire installation finished. Interpret `result.phase`: `AWAITING_RELOAD` / one-click `WAIT_RELOAD` requires the power-cycle instructions; `AWAITING_RESOURCE_RELOAD` / `WAIT_RESOURCE_RELOAD` requires resource continuation. `COMPLETE` and `LOADED` differ from these waiting states. Use `reloadguide.py` and `completion.py` for notices and completion semantics. Preserve logs and the known completed phase for `NEEDS_REVIEW`.

## Main actions

| Action | Arguments / purpose |
| --- | --- |
| `setup_all` | `workspace`, `firmware`, `power_confirmed`, `options`; install/continue |
| `usb_prepare` | Two-stage driver/service preparation |
| `driver_install`, `driver_uninstall` | Windows camera-driver binding actions |
| `direct_factory_reset` | Built-in-reference reset, independent of old LUT jobs |
| `direct_fl23_enable`, `direct_fl23_disable` | FL2/FL3 availability |
| `direct_looks_import` | `operations`: `slot`, `action=write/restore`, and for writes `path` / optional `name` |
| `compile_look` | `source`, `output`, `name`, `model` response-model path; offline conversion |
| `vertical_enable`, `vertical_disable` | Persistent display switch through the shared direct engine |
| `sound_on`, `sound_off` | Shared direct sound-switch plan |
| `sound_import` | `source`, `workspace`, `start`, `duration`, `peak`; offline audio conversion |
| `sound_volume` | `workspace`, `decibels` or `reset=true`; offline processing |
| `sound_install` | `workspace`, power confirmation; save the selected sound |
| `plugin_install` | Optional Lightroom plugin, independent of the other features |

Keep common arguments consistent with `Window.common()` and the action catalog. Do not add firmware hashes, old-job verification or a restore-before-save prerequisite in a new frontend. Conversion and volume adjustments require neither camera access nor privilege elevation.

Read the job's `worker.log` / `process.log`, use `jobs.export_support()`, and retain `paths.data_root()` as the state root. `profilelibrary.location()` resolves the paired library: `Profiles/` beside the Windows EXE, or Mac application resources. The current accepted library has 15 color pairs; three monochrome pairs were excluded. Choosing files does not re-fit profiles or call Lightroom.

See [source layout](code-map.md) / [中文接口说明](../zh-CN/frontend-contract.md).
