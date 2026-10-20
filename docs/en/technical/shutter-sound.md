# Electronic shutter sound: hardware-test candidate

[Home](../../../README.md) · [简体中文](../../zh-CN/technical/shutter-sound.md)

Branch: `feature/electronic-shutter-sound`, based on `80959db`. **One C2 2.01 owner has confirmed audible electronic-shutter sound and that Audio Signals Off silences it.** Backup, native write, full program readback and settings checks passed on Windows. Burst timing, Silent Mode and general stability remain unverified. Main and Releases are unchanged.

## Integrated command line

[shutter.py](../../../shutter.py) is the unified entry; [sound_cli.py](../../../dev/shutter_sound/sound_cli.py) implements the workflow. Use 64-bit Python 3.10+ on Windows or macOS. Mac camera USB is untested. From the extracted source root:

```text
python -m pip install -r shutter-requirements.txt
python shutter.py doctor
python shutter.py --help
```

**Independent switch:** `on` installs the electronic-capture sound branch; `off` restores that branch to stock silence. Neither changes Audio Signals, AF beeps, the custom sound files or FL23/LUT edits. Each needs USB, a normal shutdown and at least one minute with battery/USB/external power removed. This is a computer-side switch, not a new camera menu or an immediate toggle. Leave **Audio Signals (shooting) On**, Silent Mode Off and Shutter Type Electronic to hear shooting audio; the camera's global mute still takes precedence. AF-beep preservation follows the narrow CP change and settings readback; the complete integrated on/off cycle awaits physical testing.

```text
python shutter.py on --workspace sound-work --backup-copy sound-backup --firmware 2.01 --battery-percent 100
python shutter.py off --workspace sound-work
```

Replace `100` with the actual current battery percentage (at least 50). Start with new workspace/backup directories; keep them afterward. After `on`, complete the cold reload and check native sound/shooting before import. After `off`, cold reload and check electronic shutter silence **and AF beep still enabled**. Re-enabling uses `on` with the same workspace and a new internally generated job. `restore-sound` below independently removes the custom audio hook; it does not disable the electronic shutter sound feature.

**Import:** select a clip of at most two seconds. `--peak 0.4` normalizes only that clip to 40% peak; the allowed maximum is 0.5. PCM16 mono WAV needs no FFmpeg; MP3/MP4/stereo sources use FFmpeg from PATH, `--ffmpeg`, or the installed `imageio-ffmpeg` package. Specify start/duration for video or compressed audio. The source stays unchanged.

```text
python shutter.py import "sound.mp4" --workspace sound-work --start 0.26 --duration 0.15 --peak 0.4
python shutter.py audition --workspace sound-work
```

`import` is offline conversion only, with a private preview WAV. `audition` reads the body, round-trips the encoded bytes and temporarily registers them in RAM. After USB I/O ends, unplug **without switching off**, take one electronic shot and check volume, distortion, pitch/speed, shooting and playback. Record the actual result:

```text
python shutter.py confirm --workspace sound-work --result correct
```

Use `quiet`, `noise`, `wrong-speed`, `native` or `silent` instead if appropriate. Then shut down normally, wait for the access light, unplug all external power and remove the battery for at least one minute. Start up, confirm native sound/shooting/playback returned, reconnect, and record the recovery. A retained marker may survive power-off; the tool retires only that exact recovered attempt before another audition.

```text
python shutter.py confirm-recovery --workspace sound-work
python shutter.py install --workspace sound-work --battery-percent 100
```

`install` saves two compressed body-bound backups, writes/reads back two private audio files, enables the boot hook last, reads back both full programs and checks settings. It uses the **exact accepted audition bytes**, not a fresh conversion. After it ends, cold-reload again and physically check the imported sound and normal shooting/playback before:

```text
python shutter.py verify --workspace sound-work --heard-correct
python shutter.py status --workspace sound-work
```

`verify` checks loaded AP code, descriptor and files; `--heard-correct` records your actual post-boot listening result. `status` reads local records only. To restore the original sound, run `python shutter.py restore-sound --workspace sound-work`, then cold-reload and test; only the sound hook/files are reversed, preserving unrelated edits. To import another sound, restore/cold-reload first, then repeat import → audition → confirmation → recovery → install. A failure with unknown outcome stops: preserve workspace/backups and reports rather than rerunning or deleting them.

Existing developer jobs can be attached without reapplying the native patch: `python shutter.py attach --workspace sound-work --backup-copy sound-backup --native-job old-native-job --audio-job old-format0-audition`. This is offline evidence reuse, not camera verification. Keep those original directories too.

**Validation boundary:** format0 custom RAM audio is recognizable; the owner reports the 40% version is close to the source. The integrated CLI and persistent controller have offline tests, but persistent custom-audio installation/cold boot and independent off-with-AF-beep retention have not been physically verified. This branch is an experimental source tool, not a generally validated Release or Sony-signed update.

## Candidate and evidence

One two-byte CP Thumb instruction changes at file offset `0x3935ca` / runtime address `0x49b5ca`: `0021` → `0321`. Only the immediate byte differs. C2's ordinary electronic-shutter branch clears sound mode to zero after a sensor-descriptor query; the corresponding A1 II branch selects mode 3. This candidate retains the query and selects mode 3 too, using the existing kind-3 capture-sound dispatch. It edits no AP program, menu, audio setting, sound resource or calibration, and adds no runtime memory hook.

The first physical operation is a **read-only sound-registry preflight**. It must find populated kinds 1/2/3 (KA/SHA/KASHA) in native AP sound entries 0–5, which the original Audio Signals Off policy unregisters. The tested body had kinds 1/2/3 at entries 0/1/2, priority 6, with 128/1216/1216-byte buffers. A mismatch stops before firmware writes. Silent Mode and capture timing still need physical tests.

| Offline check | Result and boundary |
|---|---|
| [AP/CP input fragments](../../../dev/shutter_sound/verify_selector_inputs.py) | Eight combinations propagate an electronic request to ordinary selector 1; six check precedence. Executes the actual model-feature lookup, setter and snapshot-copy instructions. Async propagation is not simulated. |
| [Selector differential](../../../dev/shutter_sound/trace_selector.py) | 300 synthetic cases / 600 original-and-trial executions. Other selectors, skip/defer guards and counter policy remain intact; async consumers are not fully simulated. |
| Original AP audio policy | Four traces observe registration arguments. The physical test confirmed On produces sound and Off silences it; fresh registry binding remains required. |
| [Compiled transaction](../../../dev/shutter_sound/verify_worker.py) | 18 syscall-emulation cases: preflight, write, inverse, partial I/O, conflicts, readback corruption, rollback success/failure and mount failures. No camera/power-loss model. |
| [Compiled reader](../../../dev/shutter_sound/verify_probe.py) | Six synthetic-process tests plus one successful live sound-registry preflight. |
| Unit/workflow tests | 49 passed; workflow transport is mocked. |

C2 has 71 registry rows and 11 backed PIN resources, including KA/SHA/10fps; A1 II has 73 rows and 9 backed PIN resources. Concrete ranges match `SysSound.bin` byte for byte. File presence is not playback proof. The [A1 II feature](https://helpguide.sony.net/ilc/2440/v1/en/contents/231h_audio_signal_volume.html) is the donor reference; C2 [Silent Mode](https://helpguide.sony.net/ilc/2360/v1/en/contents/0414D_silent_mode_setting.html) must continue to disable shooting sounds.

## Offline reproduction

From this branch's repository root, using Python 3.10+ and privately extracted C2 2.01 components:

```text
python -m pip install -r dev/shutter_sound/requirements.txt
python dev/shutter_sound/verify_selector_inputs.py --ap appFw.so --cp cpapp-b.bin --output inputs.private.json
python dev/shutter_sound/trace_selector.py cpapp-b.bin --output selector.private.json
python dev/shutter_sound/candidate.py --ap appFw.so --cp cpapp-b.bin --output private-candidate
python dev/shutter_sound/verify_worker.py --plan private-candidate/plan.private.json --output transaction.private.json
python dev/shutter_sound/verify_probe.py --worker private-candidate/probe.so --ap appFw.so --output reader.private.json
python -m unittest discover -s dev/shutter_sound/tests -v
```

[candidate.py](../../../dev/shutter_sound/candidate.py) never opens USB. Relevant instruction conflicts stop preparation, without whole-firmware hash admission. Output includes a private CP candidate and native transaction, read-only registry and retained-image workers; it is not a Sony-signed SD-card update.

## Controlled physical test

These [developer trial commands](../../../dev/shutter_sound/trial.py) are separate from the FL23/LUT tools. Use the existing [USB setup](../fl23.md), a fully charged battery and stable connection. First select P/A/S/M, electronic shutter, Silent Mode Off and Audio Signals On, noting the original settings.

Menu paths: **Shooting → Shutter/Silent → Silent Mode Settings → Silent Mode → Off**; **Shooting → Shutter/Silent → Shutter Type → Electronic Shutter**; **Setup → Sound Option → Audio signals (shooting) → On**. Turn Silent Mode off first because it locks shooting audio off. Listen for the full-press capture sound separately from the half-press AF beep. No sound-type picker was added.

```text
python dev/shutter_sound/trial.py preflight --firmware 2.01 --job private-shutter-job --backup-copy separate-backup-folder
python dev/shutter_sound/trial.py status --job private-shutter-job
python dev/shutter_sound/trial.py apply --job private-shutter-job
```

1. **Preflight:** binds the body through the service-first USB session, reads current programs and saved/live settings, reconstructs two compressed backups, checks relevant instructions, then runs the temporary registry reader, retained-image inspection and native mode-0 program check. No firmware, shooting-setting or retained-image write. Proceed only at phase `ready`.
2. **Apply:** reads fresh programs/settings, repeats registry and native mode-0 checks, writes only the two-byte instruction, compares both complete programs with the expected fresh result and checks writable AP settings/protected CP units. Other FL23/LUT changes are preserved. No firmware SHA whitelist.
3. **Reload:** after successful readback, retained-image mode 2 uses the existing drop-then-mode-0 sequence; mode 0 is left alone. End all USB I/O, shut down normally, wait for the access light, disconnect USB/other power and remove the battery for at least one minute. Disk readback or a new kernel boot is not direct CP RAM proof.
4. **Validate:** first one electronic exposure with sound and a saved image; half-press/cancel must not add a shutter sound. Then test Lo/Hi/Hi+ bursts, sound Off, Silent Mode On, mechanical shutter/EFCS, AF beeps, movie audio, FL2/FL3/custom looks and playback. Record delay, missed/extra sounds and faults. One successful exposure does not establish stability.

Restore just this instruction, preserving later unrelated edits:

```text
python dev/shutter_sound/trial.py restore --job private-shutter-job
```

Restore also uses fresh bytes, native preflight, full readback, settings checks and retained-image handling. Unknown outcomes become `needs_review`; the CLI never blindly repeats, restores or power-cycles them. Keep the original job/native reports for inspection. This narrow inverse is separate from [complete Recovery](../recovery.md).

## Custom sound import

[custom_sound.py](../../../dev/shutter_sound/custom_sound.py) remains an **offline prototype**. Same-size native BIN replacement updates bank/resource aliases with a compressed byte inverse; a real 1,216-byte resource round-tripped exactly. This bank-replacement prototype does not validate arbitrary BIN audio; use the separately tested filter0 RAM route below.

Mono PCM16 WAV extraction produces an experimental format-1 registration template without resampling. [144 native-instruction cases](../../../dev/shutter_sound/verify_registration.py) match the original builder's 40-byte ABI for wire values 0/1. **These tests do not establish the hardware codec, sample width, channel layout or rate.** Byte21 is **priority** (native range 1–10, shutter value 6), not RT/FIFO access type; the offline prototype's previous label/default has been corrected. The native shutter trial never used that authored template. The synthetic 24kHz test is not a confirmed camera rate.

[lpcm_route.py](../../../dev/shutter_sound/lpcm_route.py) additionally tests an in-place 68-byte AP builder rewrite, without a trampoline. Its 480 cases / 960 original-and-trial executions change only enabled kind3's format byte. This rewrite remains **offline and not installed**. Existing ADPCM bytes must never be reinterpreted as PCM.

[buffer_trial.py](../../../dev/shutter_sound/buffer_trial.py) now separately exercises the original sound-loader allocation path, unit `0x70817`, without ROM changes. On the tested body, AP and CP each granted 51,200 bytes; the empty trial released both successfully. A second trial transferred a private 13,376-byte PCM clip AP→CP, cleared AP storage, transferred CP→AP, compared every byte and released both buffers. [Native ABI checks](../../../dev/shutter_sound/verify_buffer_abi.py) execute the original allocation and future-wait instructions; [compiled-worker checks](../../../dev/shutter_sound/verify_buffer_worker.py) simulate failures without live device I/O. These checks explicitly expose the native functions' unbounded waits; an unknown outcome is never retried.

A third physical trial repeated the byte comparison, unregistered kind3 and registered the owned CP buffer with wire format1, using lower-level PCM16 audio. Both registration calls returned success, but the owner heard **noise or wrong sound**, while shooting remained normal. The AP buffer was released; CP storage was retained to avoid freeing a potential playback buffer. Firmware, AP's original descriptor table and shooting settings were not changed. After cold power-off, the owner confirmed **native sound, shooting and playback returned to normal**. The PCM16/format1 live `--temporary-register` path is disabled; offline reproduction and non-playing buffer round trips remain available. The separate native-block candidate below does not replay this failed PCM16 route. This is **not persistent custom-sound import**. No asynchronous callback points into the temporary worker; a session marker prevents stacked retained buffers.

The owner clarified that the result was **hissing/crackling**, not recognizable audio at the wrong speed. [trace_playback.py](../../../dev/shutter_sound/trace_playback.py) runs the original CP PIN descriptor constructor/lookup in 16 offline cases: it preserves format1 into the next playback descriptor. Original CP debug usage also names 0=ADPCM / 1=LPCM. This does **not** prove that the physical capture used this constructor or that its decoder accepts mono little-endian PCM16; byte order, sample width, channels, rate and downstream behavior remain unresolved. The extra 64 bytes in this descriptor increase buffer capacity; they do not advance the source pointer.

Identical 66,368-byte `SysSound.bin` copies exist in rootfs and `nflasha8`; active loading/caching is unresolved. **Neither copy was replaced.** The private clip and generated workers remain local; no Sony bank or user media is distributed.

### Next candidate and persistence research

The failed **PCM16/format1** live route remains disabled. [native_codec.py](../../../dev/shutter_sound/native_codec.py) provides a separate format0 encoder based on native 32-byte blocks: one control byte and 31 signed residual bytes. Encoding uses filter0 only, avoiding the uncertain filter1 predictor. The selected clip becomes 3,776 bytes at an **assumed**, unverified 24kHz; its software round trip has about 46dB SNR. The owner recognized the selected sound in a RAM trial, but found its 12% peak too quiet. After owner-confirmed cold recovery, a 40% peak version was loaded with an exact AP→CP→AP byte comparison and successful registration. The owner reports it is close to the selected source; a complete volume/distortion/shooting/playback acceptance statement is still pending. Recognizable playback does not establish the exact hardware sample rate or persistent boot safety.

```text
python dev/shutter_sound/native_codec.py encode --wav selected.wav --assumed-rate 24000 --output private-native
python dev/shutter_sound/buffer_trial.py allocate-release --job private-native-trial --native-sound-job original-native-job --native-bin private-native/custom-native.private.bin --temporary-register
```

After all USB I/O ends, disconnect USB **without switching off**, take one electronic exposure with Audio Signals left On, and report volume, distortion, content/pitch/speed and shooting/playback. Record an actual correct result with `buffer_trial.py confirm --job private-native-trial --result correct`; otherwise use `quiet`, `noise`, `wrong-speed`, `native` or `silent`. This command is offline and never guesses a listening result. `native_codec.py encode --peak 0.4` sets the selected clip's peak ceiling; its default is 0.12 and it does not change global camera gain.

Before another trial, cold power-off and confirm native sound and normal shooting/playback, then record `buffer_trial.py confirm-recovery --job private-native-trial`. The temporary marker can survive a cold reset. The next `allocate-release` must use a fresh job and `--after-recovered-job private-native-trial`; it retires only the same body's exact prior marker/token after recorded owner recovery. It never frees an old CP buffer or deletes an unknown marker. Five marker-recovery unit cases and 14 compiled-worker cases passed; the complete sound unit suite has 49 passing cases.

[boot_sound.py](../../../dev/shutter_sound/boot_sound.py) builds an **offline persistent candidate**, and [boot_trial.py](../../../dev/shutter_sound/boot_trial.py) implements its developer install/restore/verify controller. It requires a body-bound owner-confirmed format0 trial of the identical payload before installation. The candidate reuses the original single-row CSV reader and original boot file-loader for kind3. [Reader/boot checks](../../../dev/shutter_sound/verify_beeplist.py) confirm only the selected descriptor changes and missing/oversized CSV preserves the native bank. The CSV work buffer is reduced to 2KiB, with a 2,704-byte frame instead of reserving another seven stack pages. [Original file-loader traces](../../../dev/shutter_sound/verify_file_loader.py) preserve its CP lease and use actual file length for registration. These are offline traces with simulated libc/hardware calls, not camera-boot proof.

The persistent candidate uses two new private files, `custom-shutter.bin` and `custom.txt` under `/usr/share/avsystemsound`, plus 82 guarded AP bytes; the CP program, sound bank and other descriptors are preserved. The [file worker](../../../dev/shutter_sound/files_worker.py) has [15 compiled fault cases](../../../dev/shutter_sound/verify_sound_files.py). Files are created/read back **before** enabling the boot hook, which is written last. Restore disables/reads back the hook **before** deleting files, preserving later unrelated program edits. Unknown outcomes stop without retries or file deletion. Loaded-code guards and a file-backed kind3 CP handle are checked separately from full disk readback and owner listening. **No persistent custom-audio version has been installed or boot-tested yet.** The native loader's missing/corrupt audio-file behavior remains a limitation; this developer candidate is not a Release tool.

## Reference boundary

[service-preload](https://github.com/YuuLuo/a7c2-service-preload/tree/1619f938663a36d41e72302a8cfee89a0f6acd1a), pinned at `1619f938663a36d41e72302a8cfee89a0f6acd1a`, documents USB/Senser/Jiritsu and one-shot root-child preload, not shutter sound. This candidate uses this repository's existing temporary `libJit.so` transaction loader, without permanent preload. No upstream implementation or Sony audio is copied; the reference documentation uses CC BY-SA 4.0. Keep firmware, audio, body backups and generated reports private.
