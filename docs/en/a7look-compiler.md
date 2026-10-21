# DCP / LUT → A7Look (standalone offline conversion)

[Desktop guide](desktop.md) · [简体中文](../zh-CN/a7look-compiler.md)

Choose a Sony ILCE-7CM2 `.dcp` or a compatible `.cube`, enter a name and a new `.a7look` output path, then generate. Lightroom, LR, Node, rendering plugins, renderer configuration and network access are not required. Conversion never opens the camera.

DCP conversion evaluates LookTable and ProfileToneCurve locally and fits the supported camera stages using the bundled ST mapping and measured-response model. Sensor matrices and HueSat calibration from the source profile are not transplanted. This approximates the look; it is not the complete Adobe RAW renderer. The shared mapping covers a measured scene, and preview/photo acceptance remains separate. Unsupported color stages, a wrong target model or malformed profiles produce explicit errors.

Direct CUBE input must be Sony ST / sRGB and output must be sRGB. Bake appropriate transforms first for S-Log3 or another input. [Formats](lut-formats.md).

```text
python a7look_compile.py "MyProfile.dcp" --name "My Look" --output "My Look.a7look"
```

The output includes native photo stages and the 1215-byte correction table, accepted by the custom-look writer. Existing outputs are not silently overwritten. Original DCP provenance and rights are retained.

The LrC automatic-recognition plugin installer is a separate optional entry for RAW users. Conversion, camera installation/recovery, sound and Vertical Display do not depend on it.
