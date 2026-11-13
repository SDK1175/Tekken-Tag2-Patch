#!/usr/bin/env python3
"""Package a Tag2 port build for the current RPCS3 master.

Takes a folder that already holds a working RPCS3 Windows build (rpcs3.exe built from
this source tree plus the DLLs/qt6 folder deployed next to it, e.g. the official
RPCS3 deps that windeployqt/CI produce) and turns it into a Tag2 install:

  * copies GREEN_GGPO_SIMPLE_3F/* and patches/patch.yml from the old Tag2 R20 zip
  * writes green_rollback defaults (frame display off, 3 rollback frames)
  * writes TAG2_NATIVE/NOTICE.txt
  * writes TAG2_NATIVE/release.json with the SHA-256 of every managed file
    (the list is read from rpcs3/rpcs3qt/tag2_native_policy.inc so it always
    matches what the launcher checks)
  * optionally zips the result

Usage (Windows or Linux, Python 3.8+):
  python tag2-port/make_release.py --build C:\\rpcs3\\bin (--tag2-zip Tag2_Integrated_R20.zip | --tag2-dir r20-data)
         [--sequence 21] [--zip Tag2_Port_R21.zip]

Nothing outside --build is modified. Existing green_rollback/*.txt files are kept.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
POLICY = ROOT / "rpcs3" / "rpcs3qt" / "tag2_native_policy.inc"
PACKAGE_H = ROOT / "rpcs3" / "rpcs3qt" / "tag2_native_package.h"
MANIFEST = "TAG2_NATIVE/release.json"

# Files taken verbatim from the original Tag2 R20 release zip.
FROM_TAG2_ZIP = [
    "GREEN_GGPO_SIMPLE_3F/release.json",
    "GREEN_GGPO_SIMPLE_3F/release_pin.py",
    "patches/patch.yml",
]

DEFAULTS = {
    "green_rollback/framedata_enabled.txt": b"0\n",  # optional frame display off
    "green_rollback/rollback_frames.txt": b"3\n",    # 3 / 5 / 8
}

NOTICE = """태그2 통합패치 — 최신 RPCS3 포팅판 (비공식)
Unofficial modified RPCS3 build; not an official RPCS3 release.
RPCS3 and this integration: GPL-2.0-only, except files carrying other licenses.
Upstream: https://github.com/RPCS3/rpcs3
Base commit: {base}
Tag2 changes: Tag2 Integrated R20 (tag2-integrated-20261111-r20), rebased onto the commit above.
Runtime: official RPCS3 Windows dependencies (Qt 6.12, FFmpeg avcodec-63), runtime_abi {abi}.
Not included: the legacy U1 delay engine (rpcs3-u1.exe); rpcs3.exe keeps native delay and rollback modes.
Automatic Tag2 updates are disabled in this build (the original update channel targets the old runtime).
No games, firmware, decryption keys, accounts or save data are included.
"""


def policy_paths():
    text = POLICY.read_text(encoding="utf-8")
    block = text.split("managed_paths", 1)[1].split("};", 1)[0]
    paths = re.findall(r'QStringLiteral\("([^"]+)"\)', block)
    if not paths:
        sys.exit("could not read managed_paths from " + str(POLICY))
    return paths


def runtime_abi():
    m = re.search(r'runtime_abi\s*=\s*"([^"]+)"', PACKAGE_H.read_text(encoding="utf-8"))
    if not m:
        sys.exit("could not read runtime_abi from " + str(PACKAGE_H))
    return m.group(1)


def policy_of(path):
    if path == "green_rollback/rollback_frames.txt":
        return "frames"
    if path == "green_rollback/framedata_enabled.txt":
        return "if_missing"
    return "replace"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_member(name):
    p = pathlib.PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts:
        sys.exit("unsafe path in zip: " + name)
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", required=True, help="folder with rpcs3.exe and its deployed DLLs")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--tag2-zip", help="original Tag2_Integrated_R20.zip")
    src.add_argument("--tag2-dir", help="folder holding the same files as the R20 zip (patches/patch.yml, GREEN_GGPO_SIMPLE_3F/...)")
    ap.add_argument("--sequence", type=int, default=21, help="release sequence number (default 21)")
    ap.add_argument("--base", default="9b8974d32e73c897a5fcd6bdf69413ca7e436b01", help="upstream base commit")
    ap.add_argument("--zip", help="also write the finished install as this zip")
    a = ap.parse_args()

    build = pathlib.Path(a.build).resolve()
    if not (build / "rpcs3.exe").is_file():
        sys.exit(f"{build} has no rpcs3.exe")

    # 1. Files from the old Tag2 release.
    if a.tag2_zip:
        with zipfile.ZipFile(a.tag2_zip) as z:
            names = {safe_member(n).as_posix(): n for n in z.namelist()}
            payload = {}
            for rel in FROM_TAG2_ZIP:
                if rel not in names:
                    sys.exit(f"{a.tag2_zip} does not contain {rel}")
                payload[rel] = z.read(names[rel])
    else:
        src_dir = pathlib.Path(a.tag2_dir)
        payload = {}
        for rel in FROM_TAG2_ZIP:
            p = src_dir / rel
            if not p.is_file():
                sys.exit(f"{src_dir} does not contain {rel}")
            payload[rel] = p.read_bytes()
    for rel, data in payload.items():
        dst = build / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)

    # 2. Defaults that must never overwrite a user's choice.
    for rel, data in DEFAULTS.items():
        dst = build / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)

    # 3. The legacy U1 engine cannot run with the new runtime DLLs.
    u1 = build / "rpcs3-u1.exe"
    if u1.exists():
        print("note: rpcs3-u1.exe present; it is not managed by this release and needs the old Qt 6.10.2 runtime")

    abi = runtime_abi()
    (build / "TAG2_NATIVE").mkdir(exist_ok=True)
    (build / "TAG2_NATIVE/NOTICE.txt").write_text(NOTICE.format(base=a.base, abi=abi), encoding="utf-8", newline="\n")

    # 4. Manifest over exactly the managed set.
    missing, files = [], []
    for rel in sorted(policy_paths()):
        p = build / rel
        if not p.is_file():
            missing.append(rel)
            continue
        files.append({"path": rel, "sha256": sha256(p), "policy": policy_of(rel)})
    if missing:
        print("These managed files are missing from the build folder:", file=sys.stderr)
        for m in missing:
            print("  " + m, file=sys.stderr)
        print("Deploy the official RPCS3 runtime next to rpcs3.exe (copy the DLLs and qt6/ folder from an"
              " official RPCS3 build of the same Qt/FFmpeg version) and run again.", file=sys.stderr)
        sys.exit(1)

    date = datetime.date.today().strftime("%Y%m%d")
    manifest = {
        "schema": 2,
        "sequence": a.sequence,
        "release_id": f"TAG2-RPCS3-{date}-R{a.sequence}",
        "runtime_abi": abi,
        "files": files,
    }
    out = build / MANIFEST
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(files)} files, {manifest['release_id']})")

    if a.zip:
        with zipfile.ZipFile(a.zip, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(build.rglob("*")):
                rel = p.relative_to(build).as_posix()
                if p.is_file() and not rel.startswith(("config/", "dev_", "cache/", "log/", "games/", "savestates/")):
                    z.write(p, rel)
        print("wrote", a.zip)


if __name__ == "__main__":
    main()
