import os
import subprocess
from PIL import Image
from pathlib import Path

print("=== IKA AUTO-BUILDER ===")

# ---------------------------------------------------------
# 1. Locate Downloads folder
# ---------------------------------------------------------
DOWNLOADS = Path.home() / "Downloads"
print(f"[*] Downloads folder found: {DOWNLOADS}")

APP_NAME = DOWNLOADS / "Fysonworks IKA.py"
PNG_ICON = DOWNLOADS / "ioc.png"
ICO_ICON = DOWNLOADS / "Ika.ico"

# ---------------------------------------------------------
# 2. Convert PNG → ICO
# ---------------------------------------------------------
def make_ico():
    print("[*] Converting ioc.png to Ika.ico...")
    if not PNG_ICON.exists():
        print(f"[ERROR] Icon file not found: {PNG_ICON}")
        return

    img = Image.open(PNG_ICON)
    img.save(ICO_ICON, format="ICO", sizes=[
        (256,256),(128,128),(64,64),(48,48),
        (32,32),(24,24),(16,16)
    ])
    print(f"[✓] Icon created: {ICO_ICON}")

# ---------------------------------------------------------
# 3. Build EXE using python -m PyInstaller
# ---------------------------------------------------------
def build_exe():
    print("[*] Running PyInstaller via python -m ...")

    if not APP_NAME.exists():
        print(f"[ERROR] Could not find your app: {APP_NAME}")
        return

    cmd = [
        "python",
        "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--icon={ICO_ICON}",
        str(APP_NAME)
    ]

    print("[*] Command running:", " ".join(cmd))
    subprocess.run(cmd, shell=True)

    print("\n[✓] Build complete!")
    print("Your EXE is inside the /dist/ folder next to this script.")

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    make_ico()
    build_exe()
    print("\nDone! You can close this window.")
