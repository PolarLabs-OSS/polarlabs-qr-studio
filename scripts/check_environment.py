"""Validate native architecture and GUI dependencies of the runner."""
import platform
import sys
import sysconfig
import tkinter
import customtkinter
import PIL
import qrcode
import resvg_py
import zxingcpp
import PyInstaller

expected_arch = sys.argv[1] if len(sys.argv) > 1 else None
platform_tag = sysconfig.get_platform().lower()
native_arch = (
    "arm64" if ("aarch64" in platform_tag or "arm64" in platform_tag)
    else "x64" if ("x86_64" in platform_tag or "amd64" in platform_tag)
    else platform_tag
)
print("PLATFORM",platform.platform())
print("ARCHITECTURE",platform.machine(),sysconfig.get_platform(),native_arch)
print("PYTHON",sys.version)
print("TK",tkinter.TkVersion)
print("CUSTOMTKINTER",customtkinter.__version__)
print("PYINSTALLER",PyInstaller.__version__)
if expected_arch is not None:
    assert native_arch==expected_arch, f"Wrong interpreter architecture: {native_arch} != {expected_arch}"
