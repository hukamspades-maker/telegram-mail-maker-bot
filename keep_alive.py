import subprocess
import time
import sys
import os

print("🚀 Starting Bot Supervisor (Auto-Restarter)...")

base_dir = os.path.dirname(os.path.abspath(__file__))

while True:
    try:
        print("⚡ Launching main.py...")
        p = subprocess.Popen([sys.executable, "main.py"], cwd=base_dir)
        p.wait()
        print(f"⚠️ Process exited with code {p.returncode}. Restarting in 3 seconds...")
        time.sleep(3)
    except Exception as e:
        print(f"Supervisor error: {e}")
        time.sleep(5)
