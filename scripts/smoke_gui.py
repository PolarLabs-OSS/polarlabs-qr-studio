"""Check source GUI startup and confirm packaged executable stays running."""
import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
a=argparse.ArgumentParser()
g=a.add_mutually_exclusive_group(required=True)
g.add_argument("--windows",action="store_true")
g.add_argument("--linux",action="store_true")
args=a.parse_args()

from studio import QRStudio
app=QRStudio()
app.update_idletasks()
app.update()
print(f"GUI_INIT_OK {app.winfo_geometry()}",flush=True)
app.destroy()

exe=ROOT/"dist"/("PolarLabs-QR-Studio.exe" if args.windows else "PolarLabs-QR-Studio")
if not exe.is_file():
    raise RuntimeError(f"Executable missing: {exe}")
if not args.windows:
    exe.chmod(0o755)
proc=subprocess.Popen([str(exe)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
    # PyInstaller one-file extract+launch can take several seconds.
    for i in range(14):
        time.sleep(1)
        if proc.poll() is not None:
            out,err=proc.communicate()
            raise RuntimeError(
                f"Executable exited early ({proc.returncode}) "
                f"stdout={out[-500:].decode(errors='replace')} "
                f"stderr={err[-1000:].decode(errors='replace')}"
            )
    print("BUNDLED_APP_SMOKE_OK",platform.system(),platform.machine(),exe.stat().st_size,flush=True)
finally:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
