"""
Atomic promotion of the validated 2026-07-16_utharsika_v001 staging file
to its final, never-existed-before output path. Refuses to run if the
target already exists (per the versioning rule: never overwrite a prior
version file).
"""
import hashlib
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
STAGING_PATH = os.path.join(ROOT, "09_OUTPUTS", "staging", "2026-07-16_utharsika_v001.staging.html")
TARGET_PATH = os.path.join(ROOT, "09_OUTPUTS", "2026-07-16_utharsika_v001.html")
TEMP_PATH = TARGET_PATH + ".tmp"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.exists(TARGET_PATH):
        raise RuntimeError("OUTPUT_VERSION_ALREADY_EXISTS")

    if not os.path.exists(STAGING_PATH):
        raise RuntimeError(f"STOP: staging file not found: {STAGING_PATH}")
    staging_hash = sha256_of(STAGING_PATH)
    print(f"Staging file: {STAGING_PATH}")
    print(f"Staging SHA-256: {staging_hash}")

    with open(STAGING_PATH, "rb") as src, open(TEMP_PATH, "wb") as dst:
        dst.write(src.read())
    temp_hash = sha256_of(TEMP_PATH)
    if temp_hash != staging_hash:
        os.remove(TEMP_PATH)
        raise RuntimeError(f"STOP: temp file hash ({temp_hash}) does not match staging hash ({staging_hash})")

    os.rename(TEMP_PATH, TARGET_PATH)  # rename, not replace - fails if target exists (extra safety on top of the pre-check)
    print(f"Created: {TARGET_PATH}")

    final_hash = sha256_of(TARGET_PATH)
    if final_hash != staging_hash:
        raise RuntimeError(f"STOP: final hash ({final_hash}) does not match staging hash ({staging_hash})")
    print(f"Final SHA-256 (re-read, matches staging): {final_hash}")
    print(f"Final byte size: {os.path.getsize(TARGET_PATH)}")


if __name__ == "__main__":
    main()
