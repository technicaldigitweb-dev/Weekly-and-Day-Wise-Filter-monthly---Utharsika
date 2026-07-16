"""
One-off atomic promotion script for REQ-02-D01: moves the validated
staging HTML to its final 09_OUTPUTS path. Does not touch ph_task, does
not touch any other existing file. Refuses to run if the target path
already exists.
"""

import hashlib
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
STAGING_PATH = os.path.join(ROOT, "09_OUTPUTS", "staging", "2026-07-15_utharsika_v004.staging.html")
FINAL_PATH = os.path.join(ROOT, "09_OUTPUTS", "2026-07-15_utharsika_v004.html")
TEMP_PATH = FINAL_PATH + ".tmp"

BASELINE_HASHES = {
    "2026-07-09_utharsika_v001.html": "52667eebadb04234f098af67d48d6005402f36e9f4e7b9e7ecdeb0cdc736aa9b",
    "2026-07-10_utharsika_v001.html": "335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4",
    "2026-07-10_utharsika_v002.html": "0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72",
    "2026-07-14_utharsika_v002.html": "16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684",
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.exists(FINAL_PATH):
        raise RuntimeError(f"STOP: final path already exists, refusing to overwrite: {FINAL_PATH}")
    if not os.path.exists(STAGING_PATH):
        raise RuntimeError(f"STOP: staging path does not exist: {STAGING_PATH}")

    staging_hash = sha256_of(STAGING_PATH)
    print(f"Staging file: {STAGING_PATH}")
    print(f"Staging SHA-256: {staging_hash}")

    # 1. write to a temp file (same directory -> same filesystem, so the
    #    final rename is atomic)
    with open(STAGING_PATH, "rb") as src, open(TEMP_PATH, "wb") as dst:
        dst.write(src.read())

    temp_hash = sha256_of(TEMP_PATH)
    if temp_hash != staging_hash:
        os.remove(TEMP_PATH)
        raise RuntimeError(f"STOP: temp file hash ({temp_hash}) does not match staging hash ({staging_hash})")

    # 2. re-confirm target still does not exist immediately before the move
    if os.path.exists(FINAL_PATH):
        os.remove(TEMP_PATH)
        raise RuntimeError(f"STOP: final path appeared during promotion, refusing to overwrite: {FINAL_PATH}")

    # 3. atomic move - os.rename on Windows raises FileExistsError if the
    #    destination already exists (unlike POSIX rename), which is an
    #    extra safety net on top of the explicit checks above.
    os.rename(TEMP_PATH, FINAL_PATH)
    print(f"Promoted to: {FINAL_PATH}")

    # 4. re-read the final file and confirm the hash is unchanged
    final_hash = sha256_of(FINAL_PATH)
    if final_hash != staging_hash:
        raise RuntimeError(f"STOP: final file hash ({final_hash}) does not match staging-approved hash ({staging_hash}) after promotion")
    print(f"Final SHA-256 (re-read, matches staging): {final_hash}")
    print(f"Final byte size: {os.path.getsize(FINAL_PATH)}")

    # 5. confirm every pre-existing historical HTML is byte-for-byte unchanged
    outputs_dir = os.path.join(ROOT, "09_OUTPUTS")
    all_unchanged = True
    for name, expected_hash in BASELINE_HASHES.items():
        path = os.path.join(outputs_dir, name)
        actual_hash = sha256_of(path)
        status = "UNCHANGED" if actual_hash == expected_hash else "CHANGED!!"
        if actual_hash != expected_hash:
            all_unchanged = False
        print(f"{name}: {status} ({actual_hash})")

    if not all_unchanged:
        raise RuntimeError("STOP: a historical HTML file changed during promotion - this must never happen.")

    print("\nAll historical HTML files confirmed unchanged. Promotion complete.")


if __name__ == "__main__":
    main()
