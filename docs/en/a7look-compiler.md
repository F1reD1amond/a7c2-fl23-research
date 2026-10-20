# Compile DCP / LUT into A7Look (experimental)

[简体中文](../zh-CN/a7look-compiler.md) · [Three tools and current status](a7look-suite.md)

The compiler takes a **Sony A7C II DCP or a 3D CUBE with an explicit input-space contract** and writes an `.a7look` containing native tone, matrix and chroma parameters plus the complete native correction table. It needs neither an AI nor a new chart photograph for each profile. Camera installation is separate; compilation never opens USB.

## Supported inputs

| Input | Current support |
|---|---|
| Standalone 3D `.cube` | 2–129 points per axis, including 17³, 33³, and 65³; trilinear interpolation |
| 1D `.cube`, or combined 1D shaper + 3D | Unsupported; bake into a standalone 3D CUBE first |
| `.3dl`, `.csp`, `.look`, `.vlt`, `.mga`, `.clf` / `.ctf`, HALD image LUTs | Not read directly; export a compatible CUBE using another application |
| `.dcp` | Profiles targeting `Sony ILCE-7CM2`; other camera models cannot be used directly |
| Lightroom `.xmp` presets, ICC / ICM | Not compiler inputs |

CUBE syntax supports `TITLE`, `#` comments, `DOMAIN_MIN` / `DOMAIN_MAX`, UTF-8 BOM, and Windows line endings. Extra headers such as `LUT_3D_INPUT_RANGE` are not supported.

**Readable syntax does not establish a color-space match.** Direct input must explicitly be Sony ST/sRGB. S-Log, F-Log, LogC, ACES, and other inputs require a correct ST-to-LUT-input conversion; the LUT output must already be converted to sRGB. Rec.709/Gamma 2.4 is not interchangeable with sRGB. Filenames and `TITLE` do not trigger automatic space detection.

A high-resolution source is fitted into the camera's supported tone/matrix/chroma/correction representation. Its complete 65³ or 129³ grid is not stored unchanged in the camera.

## Run

For DCP input: Python 3.10+, Lightroom Classic, and an installed/enabled [Lightroom MCP plugin and bridge](https://github.com/Automaat/lightroom-mcp). The bridge serves as a programmatic renderer; no AI client is required.

1. In the tool folder, install the Python dependencies:

   ```text
   python -m pip install -r requirements.txt
   ```

2. Place the supplied response snapshot at `calibration/a7c2-2.01.virtual.npz`. It contains numerical measured responses, without source photographs, complete firmware or camera backups. This experimental snapshot covers one 2.01 body, ISO800 and a chart at 5000K.

3. If needed, install Node.js 18+ and run these commands in the tool folder, then reopen Lightroom and enable the plugin:

   ```text
   npm install --prefix renderer @mskalski/lightroom-mcp
   node renderer/node_modules/@mskalski/lightroom-mcp/dist/index.js install-plugin
   ```

   Create `a7look-compiler.local.json` beside the entrypoint. Windows and macOS use the same format; an existing bridge can also use an absolute path:

   ```json
   {
     "renderer_command": ["node", "renderer/node_modules/@mskalski/lightroom-mcp/dist/index.js"]
   }
   ```

4. Open Lightroom Classic and run in the tool folder:

   ```text
   python a7look_compile.py "MyProfile.dcp" --name "My Look" --output "My Look.a7look"
   ```

For a larger compute budget:

```text
python a7look_compile.py "MyProfile.dcp" --name "My Look" --output "My Look.a7look" --passes 12 --evaluations 200 --extra-colors 768
```

`--passes` sets the number of candidate fits, `--evaluations` sets each solve's evaluation budget, and `--extra-colors` adds virtual colors interpolated within measured input colors. These options do not change table precision. Defaults are 3 passes, 100 evaluations per solve and 256 extra colors.

From pass 4 onward, the optimizer also tries a robust loss that reduces the influence of large-error patches. Validation still selects the candidate. More computation does not guarantee improvement on every pass; better known candidates are retained.

## Processing

**DCP → generated numerical RAW → actual Lightroom DCP rendering → measured camera-response prediction → joint native tone/matrix/chroma/correction fit → `.a7look`.**

The generated RAW embeds the complete supplied DCP, so the reference does not discard HueSatMap or other rendering stages by extracting only LookTable. Fitting starts with an optimized table-only solution, then adds native controls and compares starting points/smoothness strengths. Extra passes seek better candidates. Selection uses separate target-color groups rather than training error alone.

Numerical DCP references keep Adobe lens profiles disabled (`LensProfileEnable=0`) and retain the calibrated white balance/exposure conditions. Vignetting and distortion depend on position, focal length and aperture; they belong to lens processing and must not be folded into a global creative look. Record both camera and Adobe lens-correction settings when comparing real photographs.

The adjacent `.work` folder retains the Adobe reference, per-pass checkpoints, numerical comparisons and `result.json`. The final file refits all valid virtual colors; held-out target-color predictions belong to the separately retained validation replica. Existing output files are not overwritten.

Lightroom imports generated numerical charts into the current catalog. The compiler does not change original photographs. When running from source, the dependency list is `src/looks/requirements-compiler.txt`.

## Limits

More computation can improve the numerical solution, but does not eliminate response-model error or enable unimplemented native degrees of freedom. The current basis has 3 tone, 6 matrix and 8 chroma controls, plus the complete 1,215-byte correction field.

Reported errors are **virtual-data predictions**, not newly captured camera errors, and do not include the full response-model uncertainty. Other white balances, exposures and unmeasured colors need independent validation. A7Look and DCP describe different processing pipelines; conversion in either direction requires fitting.

Native-stage output can now use the [general A7Look writer](a7look-writer.md). Compilation alone establishes neither installation nor physical acceptance.

Sources: [entrypoint](../../a7look_compile.py), [compiler](../../src/looks/looktool/compilelook.py), [optimizer](../../src/looks/looktool/nativefit.py), [response snapshot loader](../../src/looks/looktool/measuredmodel.py).

## CUBE input (no Lightroom required)

For a 3D LUT explicitly taking Sony ST/sRGB and producing sRGB:

```text
python a7look_compile.py "MyLook.cube" --input-space sony-st-srgb --name "My Look" --output "My Look.a7look"
```

Other input spaces require an explicit ST-to-input bridge: `--input-space space-name --bridge "ST-to-input.cube"`. A video log LUT is not a Sony ST LUT. Source/bridge bytes are retained and out-of-range output clipping is disclosed. Compute budgets and calibration limits match the DCP path.

CUBE compilation does not automatically produce an Adobe RAW profile. An explicitly paired A7C II DCP can be supplied with `--raw-dcp "Matching.dcp"`; matching appearance still needs validation. Four-stage files can now use the [general A7Look writer](a7look-writer.md), whose packaged slot-4 Astia entry passed preview/photo/playback acceptance on one Windows body; final six-look color accuracy remains unmeasured.
