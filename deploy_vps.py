import subprocess
import os
import sys

KEY_PATH = r"C:\Users\Pc\Downloads\ssh private indian.key"
VPS_IP = "152.67.3.91"
USER = "ubuntu"

def run_ssh(command):
    ssh_cmd = [
        "ssh",
        "-i", KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        f"{USER}@{VPS_IP}",
        command
    ]
    print(f"Executing: {command}")
    res = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    return res.returncode == 0

def main():
    print("🚀 Starting Automated VPS Deployment on Oracle Cloud (152.67.3.91)...")

    # 1. Update APT & Install prerequisites
    print("\n1️⃣ Updating packages and installing Python 3 venv & git...")
    run_ssh("sudo apt-get update -y && sudo apt-get install -y python3 python3-pip python3-venv git curl")

    # 2. Clone Repository
    print("\n2️⃣ Setting up codebase from GitHub...")
    run_ssh("rm -rf /home/ubuntu/telegram-mail-maker-bot && git clone https://github.com/hukamspades-maker/telegram-mail-maker-bot.git /home/ubuntu/telegram-mail-maker-bot")

    # 3. Create VENV & Install Requirements
    print("\n3️⃣ Creating Python Virtual Environment & installing dependencies...")
    run_ssh("cd /home/ubuntu/telegram-mail-maker-bot && python3 -m venv venv && ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt")

    # 4. Create Data Directory & Environment File
    print("\n4️⃣ Creating data directory & .env file...")
    env_content = (
        "BOT_TOKEN=8985612343:AAGy2ihloKSeND_Oq0Iy2feqpbBpIUBGqsY\\n"
        "ADMIN_IDS=8603872187\\n"
        "DEFAULT_DOMAINS=hukam.bond,jattjames.bond\\n"
        "DATABASE_PATH=/home/ubuntu/telegram-mail-maker-bot/data/mail_bot.db\\n"
        "PORT=8080\\n"
    )
    run_ssh(f"mkdir -p /home/ubuntu/telegram-mail-maker-bot/data && echo -e '{env_content}' > /home/ubuntu/telegram-mail-maker-bot/.env")

    # 5. Create Systemd 24/7 Background Service
    print("\n5️⃣ Configuring systemd background service...")
    service_file = (
        "[Unit]\\n"
        "Description=James Bond Telegram Mail Maker Bot Service\\n"
        "After=network.target\\n\\n"
        "[Service]\\n"
        "Type=simple\\n"
        "User=ubuntu\\n"
        "WorkingDirectory=/home/ubuntu/telegram-mail-maker-bot\\n"
        "ExecStart=/home/ubuntu/telegram-mail-maker-bot/venv/bin/python3 main.py\\n"
        "Restart=always\\n"
        "RestartSec=5\\n"
        "EnvironmentFile=/home/ubuntu/telegram-mail-maker-bot/.env\\n\\n"
        "[Install]\\n"
        "WantedBy=multi-user.target\\n"
    )
    run_ssh(f"echo -e '{service_file}' | sudo tee /etc/systemd/system/hukam-bot.service")

    # 6. Enable & Start Systemd Service
    print("\n6️⃣ Enabling & Starting hukam-bot service...")
    run_ssh("sudo systemctl daemon-reload && sudo systemctl enable hukam-bot && sudo systemctl restart hukam-bot")

    # 7. Verify Status & Logs
    print("\n7️⃣ Checking service status & live logs...")
    run_ssh("sudo systemctl status hukam-bot --no-pager")
    run_ssh("sudo journalctl -u hukam-bot -n 20 --no-pager")

    print("\n🎉 VPS DEPLOYMENT COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
