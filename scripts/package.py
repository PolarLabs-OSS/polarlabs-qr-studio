"""Package each native PyInstaller build as a portable desktop download."""
import argparse
import io
import os
import platform
import tarfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--version",required=True)
    a.add_argument("--os",choices=("windows","linux"),required=True)
    a.add_argument("--arch",choices=("x64","arm64"),required=True)
    args=a.parse_args()
    kind="Windows" if args.os=="windows" else "Linux"
    arch="x64" if args.arch=="x64" else "ARM64"
    binary=ROOT/"dist"/("PolarLabs-QR-Studio.exe" if args.os=="windows" else "PolarLabs-QR-Studio")
    assert binary.is_file() and binary.stat().st_size>1_000_000,(binary,"missing/empty executable")
    output=ROOT/"out"
    output.mkdir(exist_ok=True)
    name=f"PolarLabs-QR-Studio-v{args.version}-{kind}-{arch}"
    directory="PolarLabs-QR-Studio"
    docs=(
        "PolarLabs QR Studio - portable application\n"
        f"Version {args.version} | {kind} {arch}\n\n"
        "1. Extract the entire archive to a local directory.\n"
        + ("2. Double-click PolarLabs-QR-Studio.exe.\n" if args.os=="windows"
           else "2. Open a terminal in the extracted directory.\n"
                "3. Run: chmod +x PolarLabs-QR-Studio && ./PolarLabs-QR-Studio\n"
                "   Requires a Linux GUI desktop (X11/Wayland with XWayland).\n")
        + "\nThis application does not require network access or a Python installation.\n"
          "The executable is NOT signed. Do not disable OS security controls to run it.\n"
          "See README.md for source instructions, safety information and license.\n"
    ).encode("utf-8")
    inputs={
        f"{directory}/{binary.name}":binary.read_bytes(),
        f"{directory}/README.txt":docs,
        f"{directory}/LICENSE":(ROOT/"LICENSE").read_bytes(),
    }
    if args.os=="windows":
        filename=output/(name+".zip")
        with zipfile.ZipFile(filename,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=8) as pack:
            for filename_in,data in inputs.items():
                pack.writestr(filename_in,data)
    else:
        filename=output/(name+".tar.gz")
        with tarfile.open(filename,"w:gz") as pack:
            for filename_in,data in inputs.items():
                info=tarfile.TarInfo(filename_in)
                info.size=len(data)
                info.mode=0o755 if filename_in.endswith("/PolarLabs-QR-Studio") else 0o644
                pack.addfile(info,io.BytesIO(data))
    print(f"PACKAGED {filename.name} {filename.stat().st_size} bytes",flush=True)

if __name__=="__main__":
    main()
