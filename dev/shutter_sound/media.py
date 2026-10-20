"""Private audio extraction and filter0 conversion. Never opens a camera."""
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave

import native_codec

MAX_SECONDS = 2.0


def ffmpeg_path(explicit=None):
    if explicit:
        return str(Path(explicit).resolve(strict=True))
    found = shutil.which('ffmpeg')
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise ValueError('Install imageio-ffmpeg, put ffmpeg on PATH, or supply --ffmpeg') from exc


def extract(source, destination, *, start=0, duration=None, ffmpeg=None):
    source, destination = Path(source).resolve(strict=True), Path(destination)
    if not math.isfinite(start) or start < 0 or (duration is not None and
            (not math.isfinite(duration) or not 0 < duration <= MAX_SECONDS)):
        raise ValueError('Use start >= 0 and duration between 0 and 2 seconds')
    if destination.exists():
        raise ValueError('Choose a new extraction file')
    if source.suffix.lower() == '.wav':
        try:
            samples, rate = native_codec.read_wav(source)
        except (ValueError, wave.Error):
            samples = None
        if samples is not None:
            first = round(start * rate)
            last = len(samples) if duration is None else first + round(duration * rate)
            selected = samples[first:last]
            if not selected or len(selected) > round(MAX_SECONDS * rate):
                raise ValueError('Select a nonempty clip of at most 2 seconds with --start/--duration')
            native_codec.write_wav(destination, selected, rate)
            return rate, len(selected)
    if duration is None:
        raise ValueError('For video/compressed/stereo media, specify --duration (at most 2 seconds)')
    # Argument vector only: audio paths are never interpolated into shell text.
    command = [ffmpeg_path(ffmpeg), '-nostdin', '-v', 'error', '-n', '-i', str(source),
               '-ss', str(start), '-t', str(duration), '-map', '0:a:0', '-vn',
               '-ac', '1', '-ar', '44100', '-c:a', 'pcm_s16le', str(destination)]
    result = subprocess.run(command, capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError('Audio extraction failed: ' + result.stderr.decode('utf-8', errors='replace')[-1500:])
    samples, rate = native_codec.read_wav(destination)
    if not samples or len(samples) > round(MAX_SECONDS * rate):
        raise ValueError('Extracted clip is empty or exceeds 2 seconds')
    return rate, len(samples)


def convert(source, output, *, start=0, duration=None, peak=0.4, ffmpeg=None):
    root = Path(output)
    if not math.isfinite(peak) or not 0 < peak <= 0.5:
        raise ValueError('Use --peak greater than 0 and at most 0.5')
    root.mkdir(parents=True, exist_ok=False)
    wav = root / 'selected.private.wav'
    rate, frames = extract(source, wav, start=start, duration=duration, ffmpeg=ffmpeg)
    # A short edge fade avoids adding hard cut discontinuities; no source edit.
    samples, _ = native_codec.read_wav(wav)
    fade = min(round(rate * 0.002), len(samples) // 2)
    for i in range(fade):
        scale = i / fade
        samples[i] = round(samples[i] * scale)
        samples[-1 - i] = round(samples[-1 - i] * scale)
    native_codec.write_wav(wav, samples, rate)
    payload, preview, report = native_codec.candidate(wav, target_rate=24000, peak=peak)
    if not 0 < len(payload) <= 51200:
        raise ValueError('Encoded clip exceeds the native buffer capacity')
    (root / 'custom-native.private.bin').write_bytes(payload)
    native_codec.write_wav(root / 'preview.private.wav', preview, 24000)
    report.update(source=str(Path(source).resolve()), start_seconds=start,
                  duration_seconds=frames / rate, requested_peak=peak,
                  fade_seconds=fade / rate, camera_io=False)
    (root / 'conversion.private.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report
