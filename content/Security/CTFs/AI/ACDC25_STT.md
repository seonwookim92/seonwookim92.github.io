---
title: "ACDC25: STT"
date:
tags:
draft: true
---
![[ACDC25_STT-20251101214746419.png]]


![[ACDC25_STT-20251101214800934.png]]

![[ACDC25_STT-20251101214816346.png]]


```python
#!/usr/bin/env python3
import argparse
import os
import sys
import re
import json
import math
import wave
import contextlib
import subprocess
import tempfile
import shutil
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

# =====================================================
# Utilities
# =====================================================

NUM_WORDS = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "won": "1",
    "two": "2", "to": "2", "too": "2", "tu": "2",
    "three": "3", "tree": "3", "free": "3",
    "four": "4", "for": "4", "fore": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8", "ate": "8",
    "nine": "9",
}
# Note: Extendable with --extra-mapping


def which(prog: str) -> Optional[str]:
    """Check if executable exists in PATH."""
    return shutil.which(prog)


def ffprobe_duration(audio_path: str) -> Optional[float]:
    """Get audio duration using ffprobe or wave as fallback."""
    if which("ffprobe"):
        try:
            out = subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                stderr=subprocess.STDOUT
            )
            return float(out.decode().strip())
        except Exception:
            return None

    # Fallback for .wav
    try:
        if audio_path.lower().endswith(".wav"):
            with contextlib.closing(wave.open(audio_path, 'r')) as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
    except Exception:
        pass
    return None


# =====================================================
# Backend Selection
# =====================================================

def pick_backend(force: Optional[str] = None) -> str:
    """Auto-select STT backend based on availability."""
    if force:
        return force.lower()

    try:
        import vosk
        return "vosk"
    except Exception:
        pass
    try:
        import faster_whisper
        return "faster-whisper"
    except Exception:
        pass
    try:
        import whisper
        return "openai-whisper"
    except Exception:
        pass
    try:
        import speech_recognition as sr
        import pocketsphinx
        return "pocketsphinx"
    except Exception:
        pass
    return "none"


# =====================================================
# Transcription Functions
# =====================================================

def transcribe_vosk(audio_path: str, out_jsonl: str, model_path: Optional[str]) -> List[Dict[str, Any]]:
    """Transcribe using VOSK and produce word-level results."""
    import json
    import os
    from vosk import Model, KaldiRecognizer
    import subprocess
    import shlex

    if model_path is None or not os.path.isdir(model_path):
        raise RuntimeError("Vosk selected but no valid model specified.")

    # Convert to mono 16k PCM WAV
    pcm_path = audio_path
    if not audio_path.lower().endswith(".wav"):
        pcm_path = os.path.splitext(audio_path)[0] + ".16k.wav"
        cmd = f'ffmpeg -y -i {shlex.quote(audio_path)} -ac 1 -ar 16000 -f wav {shlex.quote(pcm_path)}'
        subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)

    results = []
    with contextlib.closing(wave.open(pcm_path, "rb")) as wf:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if "result" in res:
                    results.append(res)
        final = json.loads(rec.FinalResult())
        if "result" in final:
            results.append(final)

    with open(out_jsonl, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    words = []
    for r in results:
        for w in r.get("result", []):
            words.append({
                "word": w.get("word", ""),
                "start": w.get("start", 0.0),
                "end": w.get("end", 0.0)
            })
    return words


def transcribe_faster_whisper(audio_path: str, model_size: str) -> List[Dict[str, Any]]:
    """Transcribe using Faster-Whisper."""
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, vad_filter=True, word_timestamps=True, beam_size=1)

    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append({
                "word": w.word.strip(),
                "start": float(w.start),
                "end": float(w.end)
            })
    return words


def transcribe_openai_whisper(audio_path: str, model_size: str) -> List[Dict[str, Any]]:
    """Transcribe using OpenAI Whisper."""
    import whisper
    model = whisper.load_model(model_size)
    res = model.transcribe(audio_path, word_timestamps=True, verbose=False)

    words = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            words.append({
                "word": w.get("word", "").strip(),
                "start": float(w.get("start", 0.0)),
                "end": float(w.get("end", 0.0))
            })
    return words


def transcribe_pocketsphinx(audio_path: str) -> List[Dict[str, Any]]:
    """Offline speech recognition with PocketSphinx."""
    import speech_recognition as sr
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)
    text = r.recognize_sphinx(audio)

    words = []
    t = 0.0
    for token in text.split():
        words.append({"word": token, "start": t, "end": t + 0.3})
        t += 0.3
    return words


# =====================================================
# Number Extraction & Decoding
# =====================================================

def words_to_digits(words: List[Dict[str, Any]], extra_map: Dict[str, str]) -> Tuple[str, List[Tuple[str, float, float]]]:
    """Convert word tokens to digit stream."""
    digit_stream = []
    word_rows = []
    mapping = {**NUM_WORDS, **{k.lower(): v for k, v in extra_map.items()}}

    for w in words:
        token = re.sub(r"[^A-Za-z0-9]", "", (w.get("word") or "")).lower()
        if token in mapping:
            d = mapping[token]
            digit_stream.append(d)
            word_rows.append((d, float(w.get("start", 0.0)), float(w.get("end", 0.0))))
    return "".join(digit_stream), word_rows


def save_words_tsv(path: str, word_rows: List[Tuple[str, float, float]]) -> None:
    """Save per-word digit with timestamps."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("digit\tstart\tend\n")
        for d, s, e in word_rows:
            f.write(f"{d}\t{s:.3f}\t{e:.3f}\n")


def save_digits_txt(path: str, digits: str) -> None:
    """Save pure digit stream."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(digits + "\n")


def chunk_digits(digits: str, n: int) -> List[str]:
    return [digits[i:i + n] for i in range(0, len(digits), n) if len(digits[i:i + n]) == n]


def try_ascii_from_dec(digits: str) -> List[str]:
    """Try decoding 2- and 3-digit ASCII codes."""
    outs = []
    for n in (2, 3):
        out = []
        for ch in chunk_digits(digits, n):
            val = int(ch)
            out.append(chr(val) if 32 <= val <= 126 else "?")
        outs.append(f"[ASCII-{n}digit] {''.join(out)}")
    return outs


def try_ascii_word_delimited(word_rows: List[Tuple[str, float, float]]) -> List[str]:
    digits = "".join(d for d, _, __ in word_rows)
    return try_ascii_from_dec(digits)


def try_base_conversions(digits: str) -> List[str]:
    outs = []
    if set(digits) <= {"0", "1"} and len(digits) >= 8:
        bytes_arr = [digits[i:i + 8] for i in range(0, len(digits), 8) if len(digits[i:i + 8]) == 8]
        s = "".join(chr(int(b, 2)) for b in bytes_arr)
        outs.append("[BINARY/8bit] " + s)

    triples = chunk_digits(digits, 3)
    if triples:
        try:
            b = bytes(int(t) for t in triples if 0 <= int(t) <= 255)
            outs.append("[DEC/3-to-bytes] " + b.decode("utf-8", errors="replace"))
        except Exception:
            pass
    return outs


def try_common_patterns(digits: str) -> List[str]:
    """Try sliding ASCII decoding for noisy data."""
    outs = []
    for n in (2, 3):
        s = ""
        i = 0
        while i + n <= len(digits):
            val = int(digits[i:i + n])
            if 32 <= val <= 126:
                s += chr(val)
                i += n
            else:
                i += 1
                if len(s) >= 6:
                    outs.append(f"[ASCII-{n} sliding] {s}")
                    s = ""
        if len(s) >= 6:
            outs.append(f"[ASCII-{n} sliding] {s}")
    return outs


def scan_flag_like(texts: List[str]) -> List[str]:
    """Find flag-like patterns (ACDC{...})."""
    hits = []
    for t in texts:
        if re.search(r"ACDC\{[^}]{0,200}\}", t):
            hits.append(t)
    return hits


# =====================================================
# Main
# =====================================================

def main():
    ap = argparse.ArgumentParser(description="CTF Audio Number Extractor & Decoder")
    ap.add_argument("--audio", required=True, help="Path to audio file")
    ap.add_argument("--out", default="out", help="Output directory")
    ap.add_argument("--stt", default=None,
                    choices=[None, "vosk", "faster-whisper", "openai-whisper", "pocketsphinx"],
                    help="Force STT backend")
    ap.add_argument("--vosk-model", default=os.environ.get("VOSK_MODEL"),
                    help="Path to Vosk model directory")
    ap.add_argument("--whisper-size", default="base",
                    help="Model size for Whisper/Faster-Whisper")
    ap.add_argument("--extra-mapping", default=None,
                    help='JSON string dict like {"niner":"9","aught":"0"}')
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    dur = ffprobe_duration(args.audio)
    if dur:
        print(f"[i] Audio duration: {dur/3600:.2f} hours ({dur:.1f} sec)")

    backend = pick_backend(args.stt)
    if args.stt:
        backend = args.stt
    print(f"[i] Selected backend: {backend}")
    if backend == "none":
        print("[!] No STT backend available.")
        sys.exit(2)

    # --- Transcription ---
    try:
        if backend == "vosk":
            jsonl_path = os.path.join(args.out, "vosk_raw.jsonl")
            words = transcribe_vosk(args.audio, jsonl_path, args.vosk_model)
        elif backend == "faster-whisper":
            words = transcribe_faster_whisper(args.audio, args.whisper_size)
        elif backend == "openai-whisper":
            words = transcribe_openai_whisper(args.audio, args.whisper_size)
        elif backend == "pocketsphinx":
            words = transcribe_pocketsphinx(args.audio)
        else:
            raise RuntimeError("Unsupported backend selection")
    except Exception as e:
        print(f"[!] Transcription failed: {e}")
        sys.exit(3)

    # --- Extract digits ---
    extra_map = {}
    if args.extra_mapping:
        try:
            extra_map = json.loads(args.extra_mapping)
        except Exception as e:
            print(f"[!] Failed to parse --extra-mapping JSON: {e}")

    digits, word_rows = words_to_digits(words, extra_map=extra_map)

    words_path = os.path.join(args.out, "words.tsv")
    digits_path = os.path.join(args.out, "numbers.txt")
    save_words_tsv(words_path, word_rows)
    save_digits_txt(digits_path, digits)

    print(f"[i] Saved digit words with timestamps -> {words_path}")
    print(f"[i] Saved digit stream -> {digits_path} (length={len(digits)})")

    # --- Try Decoding ---
    candidates = []
    candidates += try_ascii_from_dec(digits)
    candidates += try_ascii_word_delimited(word_rows)
    candidates += try_base_conversions(digits)
    candidates += try_common_patterns(digits)

    cand_path = os.path.join(args.out, "candidates.txt")
    with open(cand_path, "w", encoding="utf-8") as f:
        for c in candidates:
            f.write(c + "\n")

    print(f"[i] Wrote decoding candidates -> {cand_path}")

    # --- Scan for flags ---
    hits = scan_flag_like(candidates)
    if hits:
        print("[✓] Potential FLAG hits found:")
        for h in hits:
            print(h)
    else:
        print("[!] No ACDC{...} found. Check candidates.txt or adjust mapping.")

if __name__ == "__main__":
    main()
```


![[ACDC25_STT-20251101214856480.png]]


`https://shorturl.at/DbzJ8`

![[ACDC25_STT-20251101214925368.png]]

