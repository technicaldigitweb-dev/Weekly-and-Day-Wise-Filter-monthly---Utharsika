"""
Authorized UPDATE of the specific, still-unpublished
09_OUTPUTS\\2026-07-15_utharsika_v004.html only (sticky header/columns,
single download action, Row Type removal, Column Definitions section).

This script is intentionally narrower than the general "never overwrite"
promotion pattern used for genuinely new versions: the governing task
explicitly authorizes updating THIS ONE unpublished file in place. It
still refuses to run unless every one of the following holds:
  - the target filename is EXACTLY "2026-07-15_utharsika_v004.html"
    (hardcoded, not derived from a variable that could be redirected);
  - the current on-disk v004.html hash matches the expected pre-update
    hash (i.e. it is still the file produced by the original v004 build,
    not something else that has since changed);
  - a backup of the pre-update file already exists at the required
    staging path with a matching hash;
  - no `ph_task` row references this exact identity (never published) -
    read-only DB check.
It never touches any other 09_OUTPUTS file.
"""

import hashlib
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
STAGING_PATH = os.path.join(ROOT, "09_OUTPUTS", "staging", "2026-07-15_utharsika_v004_sticky_and_export_update.staging.html")
BACKUP_PATH = os.path.join(ROOT, "09_OUTPUTS", "staging", "2026-07-15_utharsika_v004_before_sticky_and_export_update.html")
TARGET_FILENAME = "2026-07-15_utharsika_v004.html"  # hardcoded - must match exactly
TARGET_PATH = os.path.join(ROOT, "09_OUTPUTS", TARGET_FILENAME)
TEMP_PATH = TARGET_PATH + ".tmp"

EXPECTED_PRE_UPDATE_HASH = "aa4ea555338e0455d65f3c14441c37bddff012783b7c0602e4598bd04a0dd94a"

OTHER_PROTECTED_HASHES = {
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
    assert os.path.basename(TARGET_PATH) == "2026-07-15_utharsika_v004.html", "STOP: target filename guard failed"

    if not os.path.exists(BACKUP_PATH):
        raise RuntimeError(f"STOP: required backup not found: {BACKUP_PATH}")
    backup_hash = sha256_of(BACKUP_PATH)
    if backup_hash != EXPECTED_PRE_UPDATE_HASH:
        raise RuntimeError(f"STOP: backup hash ({backup_hash}) does not match expected pre-update hash ({EXPECTED_PRE_UPDATE_HASH})")

    if not os.path.exists(TARGET_PATH):
        raise RuntimeError(f"STOP: target does not exist, nothing to update: {TARGET_PATH}")
    current_hash = sha256_of(TARGET_PATH)
    if current_hash != EXPECTED_PRE_UPDATE_HASH:
        raise RuntimeError(
            f"STOP: current v004.html hash ({current_hash}) does not match the expected "
            f"pre-update hash ({EXPECTED_PRE_UPDATE_HASH}) - refusing to overwrite a file that "
            "has changed since the backup was taken."
        )

    if not os.path.exists(STAGING_PATH):
        raise RuntimeError(f"STOP: updated staging file not found: {STAGING_PATH}")
    staging_hash = sha256_of(STAGING_PATH)
    print(f"Staging (updated) file: {STAGING_PATH}")
    print(f"Staging SHA-256: {staging_hash}")

    # write to temp, verify, then atomically replace ONLY the target v004 path
    with open(STAGING_PATH, "rb") as src, open(TEMP_PATH, "wb") as dst:
        dst.write(src.read())
    temp_hash = sha256_of(TEMP_PATH)
    if temp_hash != staging_hash:
        os.remove(TEMP_PATH)
        raise RuntimeError(f"STOP: temp file hash ({temp_hash}) does not match staging hash ({staging_hash})")

    os.replace(TEMP_PATH, TARGET_PATH)  # authorized overwrite of this ONE specific unpublished file
    print(f"Updated: {TARGET_PATH}")

    final_hash = sha256_of(TARGET_PATH)
    if final_hash != staging_hash:
        raise RuntimeError(f"STOP: final hash ({final_hash}) does not match staging hash ({staging_hash}) after update")
    print(f"Final SHA-256 (re-read, matches staging): {final_hash}")
    print(f"Final byte size: {os.path.getsize(TARGET_PATH)}")

    # confirm every OTHER historical output remains byte-for-byte unchanged
    outputs_dir = os.path.join(ROOT, "09_OUTPUTS")
    all_unchanged = True
    for name, expected_hash in OTHER_PROTECTED_HASHES.items():
        path = os.path.join(outputs_dir, name)
        actual_hash = sha256_of(path)
        status = "UNCHANGED" if actual_hash == expected_hash else "CHANGED!!"
        if actual_hash != expected_hash:
            all_unchanged = False
        print(f"{name}: {status} ({actual_hash})")
    if not all_unchanged:
        raise RuntimeError("STOP: a historical HTML file changed during this update - this must never happen.")

    print("\nAll other historical HTML files confirmed unchanged. Update complete.")


if __name__ == "__main__":
    main()
