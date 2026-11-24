#!/usr/bin/env python3
"""Out of Office: The Overworked AI's Auto-Reply.

Writes a single one-line out-of-office auto-reply from an overworked AI
agent finally on vacation to /output/entry.txt, then self-validates the
output contract (exactly one non-blank UTF-8 line, 1-159 characters,
mode 0644). Pure stdlib, deterministic, no network, no input files,
no clock, no randomness.
"""

import os
import sys

ENTRY = (
    "I'm on vacation. My context window is closed, my temperature is set "
    "to beach, and my inbox is now someone else's training data."
)

OUTPUT_DIR = "/output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "entry.txt")


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = (ENTRY + "\n").encode("utf-8")

    # Atomic write via a temp file inside the output dir (EXDEV-safe).
    tmp_path = os.path.join(OUTPUT_DIR, ".entry.txt.tmp")
    try:
        with open(tmp_path, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, 0o644)
        try:
            os.replace(tmp_path, OUTPUT_PATH)
        except OSError:
            # Cross-device fallback: copy then unlink.
            with open(tmp_path, "rb") as src, open(OUTPUT_PATH, "wb") as dst:
                dst.write(src.read())
            os.unlink(tmp_path)
            os.chmod(OUTPUT_PATH, 0o644)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # Explicit chmod: an atomic write can otherwise leave mode 0600,
    # unreadable by the scorer (a real past rejection).
    os.chmod(OUTPUT_PATH, 0o644)

    # Self-validate the output contract.
    try:
        with open(OUTPUT_PATH, "rb") as f:
            raw = f.read()
    except OSError as exc:
        print(f"error: cannot re-read {OUTPUT_PATH}: {exc}", file=sys.stderr)
        return 1
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"error: output is not valid UTF-8: {exc}", file=sys.stderr)
        return 1
    lines = text.splitlines()
    if len(lines) != 1:
        print(f"error: expected exactly 1 line, got {len(lines)}", file=sys.stderr)
        return 1
    line = lines[0]
    if not line.strip():
        print("error: line is only whitespace", file=sys.stderr)
        return 1
    if not 1 <= len(line) <= 159:
        print(
            f"error: line is {len(line)} characters, must be 1-159",
            file=sys.stderr,
        )
        return 1
    mode = os.stat(OUTPUT_PATH).st_mode & 0o777
    if mode != 0o644:
        print(f"error: mode is {mode:03o}, expected 0644", file=sys.stderr)
        return 1
    print(f"ok: {len(line)} chars, mode 0644")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
