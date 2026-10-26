"""Release gate: ensure all expected platform assets exist and contain binaries."""
import sys
import tarfile
import zipfile
from pathlib import Path

root=Path(sys.argv[1])
expected=[
    ("PolarLabs-QR-Studio-v1.1.0-Windows-x64.zip","PolarLabs-QR-Studio.exe"),
    ("PolarLabs-QR-Studio-v1.1.0-Windows-ARM64.zip","PolarLabs-QR-Studio.exe"),
    ("PolarLabs-QR-Studio-v1.1.0-Linux-x64.tar.gz","PolarLabs-QR-Studio"),
    ("PolarLabs-QR-Studio-v1.1.0-Linux-ARM64.tar.gz","PolarLabs-QR-Studio")
]
for filename,binary in expected:
    path=root/filename
    assert path.is_file(),f"Missing artifact: {path}"
    assert path.stat().st_size>1_000_000, f"Artifact too small: {filename}"
    if filename.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            bad=z.testzip()
            assert bad is None,f"Corrupt zip: {filename}: {bad}"
            names=z.namelist()
            matches=[x for x in names if x.endswith("/"+binary)]
            assert matches and z.getinfo(matches[0]).file_size>1_000_000, filename
    else:
        with tarfile.open(path,"r:gz") as z:
            files=[m for m in z.getmembers() if m.name.endswith("/"+binary)]
            assert files and files[0].size>1_000_000,filename
    print("PASS",filename,path.stat().st_size,flush=True)
print("ALL 4 PLATFORM ARCHIVES READY")
