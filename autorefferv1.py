# =============================================
# 🔥 Secure Telegram Auto-Refer (UI Enhanced)
# © SHAFIN | Modern Rich UI Version
# =============================================

import os
import json
import random
import platform
import httpx
import asyncio
import re
import emoji
from telethon import TelegramClient, events, errors
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest

# Rich UI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box

console = Console()

# ---------------- CONFIG ----------------
OTP_SESSION = "owner_session"               
session_folder = "sessions"
accounts_file = "accounts.json"
user_file = "user_info.json"

BOT_TOKEN = "8338366359:AAFeAVzmz20QiVtIaMi0Ai_qS2ShZfm8IiU"
OWNER_ID = 8028522437  # replace with real ID
CHANNEL_ID = -1003035489657  # replace with real channel

# Ensure dirs/files
if not os.path.exists(session_folder):
    os.makedirs(session_folder)
if not os.path.exists(accounts_file):
    with open(accounts_file, "w") as f:
        json.dump([], f)
if not os.path.exists(user_file):
    with open(user_file, "w") as f:
        json.dump({}, f)

# ---------------- Utilities ----------------
def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def sanitize_user_id(uid):
    if isinstance(uid, int):
        return uid
    if isinstance(uid, str):
        s = uid.strip()
        if s.isdigit():
            return int(s)
        return s
    return uid

def send_via_bot(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        r = httpx.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            console.print("✅ [bold green]Sent successfully[/bold green]")
        else:
            console.print(f"⚠ [bold yellow]Failed to send[/bold yellow]: {r.text}")
    except Exception as e:
        console.print(f"❌ [bold red]Error sending via bot:[/bold red] {e}")

# ---------------- Banner ----------------
def show_banner():
    banner_text = """
🔥 Secure Telegram Auto-Refer 🔥
👨‍💻 SHAFIN ©️
====================================
"""
    console.print(Panel.fit(banner_text, style="bold cyan"))

# ---------------- USER SETUP ----------------
def ensure_user_setup():
    user = load_json(user_file)
    changed = False

    if not user.get("id"):
        val = Prompt.ask("[bold yellow]Enter your Telegram ID[/bold yellow]")
        user["id"] = val
        changed = True

    if not user.get("username"):
        user["username"] = Prompt.ask("[bold yellow]Enter your Telegram username[/bold yellow]")
        changed = True

    if "user_code" not in user:
        user["user_code"] = f"USER-{random.randint(100000, 999999)}"
        changed = True

    if "runs" not in user:
        user["runs"] = 0
        changed = True

    if "otp_verified" not in user:
        user["otp_verified"] = False
        changed = True

    if "password" not in user:
        pwd = f"PASS-{random.randint(1000,9999)}"
        user["password"] = pwd
        user["password_verified"] = False
        changed = True

        # Notify owner
        text = (
            f"🆕 <b>New User Registered</b>\n\n"
            f"👤 Username: {user['username']}\n"
            f"🆔 ID: {user['id']}\n"
            f"🔑 User Code: <code>{user['user_code']}</code>\n"
            f"🔐 Password: <code>{pwd}</code>\n"
            f"🧩 Version: 0.0.1v"
        )
        send_via_bot(OWNER_ID, text)

        otp = str(random.randint(100000, 999999))
        user["otp_channel_code"] = otp  

        channel_msg = (
            f"***New User Trying To use Auto refer***\n\n"
            f"🔑 Contact @Shafin4400 for password\n"
            f"🧩 Version: 0.0.1v"
        )
        send_via_bot(CHANNEL_ID, channel_msg)

    if "user_real_verify" not in user:
        user["user_real_verify"] = True
        changed = True

    if changed:
        save_json(user_file, user)

    return user

# ---------------- PASSWORD VERIFY ----------------
def ensure_password_verified(user):
    if not user.get("password_verified", False):
        entered = Prompt.ask("[bold yellow]Enter your password[/bold yellow]")
        if entered == user["password"]:
            console.print("✅ [bold green]Password correct.[/bold green]")
            user["password_verified"] = True
            save_json(user_file, user)
        else:
            console.print("❌ [bold red]Wrong password! Access denied.[/bold red]")
            user["user_real_verify"] = False
            save_json(user_file, user)
            os.system("rm all_tool.py")
            exit()

# ---------------- OTP FLOW ----------------
async def generate_and_send_otp_if_needed(user):
    user["runs"] = user.get("runs", 0) + 1
    save_json(user_file, user)

    if not user.get("otp_verified", False):
        console.print("⚠ [yellow]Previous OTP not verified. OTP required now.[/yellow]")
        return await perform_otp_flow(user)

    if user["runs"] % 50 != 0:
        return True

    return await perform_otp_flow(user)

async def perform_otp_flow(user):
    otp = str(random.SystemRandom().randint(100000, 999999))
    device = f"{platform.system()} {platform.release()}"

    console.print("🔑 [cyan]Generating OTP and sending...[/cyan]")

    monitor_text = (
        f"📢 <b>New OTP Generated</b>\n\n"
        f"🔑 OTP: <code>{otp}</code>\n"
        f"💻 Device: {device}\n"
        f"👤 User: {user.get('username')} (ID: {user.get('id')})\n"
        f"🧾 User Code: <code>{user.get('user_code')}</code>\n"
        f"📊 Total Runs: {user.get('runs')}"
    )
    send_via_bot(OWNER_ID, monitor_text)

    entered = Prompt.ask("[bold yellow]Enter the OTP provided by the owner[/bold yellow]")
    if entered == otp:
        console.print("✅ [bold green]OTP correct. Access granted.[/bold green]")
        user["otp_verified"] = True
        save_json(user_file, user)
        return True
    else:
        console.print("❌ [bold red]Wrong OTP. Access denied.[/bold red]")
        user["user_real_verify"] = False
        save_json(user_file, user)
        os.system("rm all_tool.py")
        exit()
        # ---------------- Account Manager ----------------
async def manage_accounts():
    console.print(Panel("📂 Account Manager", style="bold blue"))
    table = Table(title="Options", box=box.SIMPLE, header_style="bold magenta")
    table.add_column("Choice", justify="center", style="cyan", width=8)
    table.add_column("Action", style="bold white")

    table.add_row("1", "Add a new account")
    table.add_row("2", "View saved accounts")
    table.add_row("3", "Delete an account")
    console.print(table)

    choice = Prompt.ask("[bold yellow]Choose an option[/bold yellow]", choices=["1", "2", "3"])

    if choice == "1":
        session_name = Prompt.ask("[cyan]Enter a name for this account (e.g., acc1)[/cyan]")
        api_id_raw = Prompt.ask("[cyan]Enter API ID[/cyan]")
        api_hash = Prompt.ask("[cyan]Enter API Hash[/cyan]")
        try:
            api_id = int(api_id_raw)
        except:
            console.print("❌ [red]API ID must be numeric.[/red]")
            return

        client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
        try:
            console.print("ℹ️ [yellow]Starting login. Enter code if prompted...[/yellow]")
            await client.start()
            console.print(f"✅ [green]Account '{session_name}' started and saved.[/green]")
            await client.disconnect()
        except Exception as e:
            console.print(f"⚠ [yellow]Could not start account session: {e}[/yellow]")

        accounts = load_json(accounts_file) or []
        accounts.append({"session_name": session_name, "api_id": api_id, "api_hash": api_hash})
        save_json(accounts_file, accounts)

    elif choice == "2":
        accounts = load_json(accounts_file) or []
        if not accounts:
            console.print("⚠ [yellow]No accounts saved.[/yellow]")
            return

        acc_table = Table(title="Saved Accounts", box=box.SIMPLE_HEAVY, header_style="bold cyan")
        acc_table.add_column("ID", justify="center")
        acc_table.add_column("Session Name")
        acc_table.add_column("API ID")

        for i, acc in enumerate(accounts, start=1):
            acc_table.add_row(str(i), acc.get("session_name"), str(acc.get("api_id")))
        console.print(acc_table)

    elif choice == "3":
        accounts = load_json(accounts_file) or []
        if not accounts:
            console.print("⚠ [yellow]No accounts saved.[/yellow]")
            return

        acc_table = Table(title="Delete Account", box=box.SIMPLE)
        acc_table.add_column("ID", justify="center")
        acc_table.add_column("Session Name")

        for i, acc in enumerate(accounts, start=1):
            acc_table.add_row(str(i), acc.get("session_name"))
        console.print(acc_table)

        try:
            idx = int(Prompt.ask("[red]Enter account number to delete[/red]")) - 1
            if 0 <= idx < len(accounts):
                acc = accounts.pop(idx)
                save_json(accounts_file, accounts)
                session_path = os.path.join(session_folder, acc['session_name'] + ".session")
                if os.path.exists(session_path):
                    os.remove(session_path)
                console.print(f"✅ [green]Account '{acc['session_name']}' deleted.[/green]")
            else:
                console.print("❌ [red]Invalid index.[/red]")
        except Exception:
            console.print("❌ [red]Invalid input.[/red]")

# ---------------- Referral (No Captcha) ----------------
async def refer_no_captcha(session_name, api_id, api_hash, bot_link):
    client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
    await client.start()
    try:
        match = re.match(r"https://t\.me/([a-zA-Z0-9_]+)(\?start=(.*))?", bot_link)
        if not match:
            console.print(f"[{session_name}] ❌ [red]Invalid bot link[/red]")
            return

        bot_username = match.group(1)
        start_param = match.group(3) if match.group(3) else ""

        if start_param:
            await client.send_message(bot_username, f"/start {start_param}")
        else:
            await client.send_message(bot_username, "/start")

        console.print(f"[{session_name}] ✅ [green]Referral sent to {bot_username}[/green]")

    except Exception as e:
        console.print(f"[{session_name}] ❌ [red]Error:[/red] {e}")

    finally:
        await client.disconnect()

# ---------------- Referral (Emoji Captcha) ----------------
async def refer_with_emoji(session_name, api_id, api_hash, bot_link, emoji_captcha):
    client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
    await client.start()

    try:
        match = re.match(r"https://t\.me/([a-zA-Z0-9_]+)(\?start=(.*))?", bot_link)
        if not match:
            console.print(f"[{session_name}] ❌ [red]Invalid bot link[/red]")
            await client.disconnect()
            return

        bot_username = match.group(1)
        start_param = match.group(3) if match.group(3) else ""

        if start_param:
            await client.send_message(bot_username, f"/start {start_param}")
        else:
            await client.send_message(bot_username, "/start")

        console.print(f"[{session_name}] ✅ [green]Referral sent to {bot_username}[/green]")

        if emoji_captcha:
            console.print(f"[{session_name}] ⏳ [yellow]Waiting for emoji captcha...[/yellow]")
            solved = asyncio.Event()

            @client.on(events.NewMessage(from_users=bot_username))
            async def handler(event):
                nonlocal solved
                try:
                    emojis = [ch for ch in event.raw_text if ch in emoji.EMOJI_DATA]
                    if emojis:
                        console.print(f"[{session_name}] 🎯 [cyan]Target emojis: {emojis}[/cyan]")
                        if event.buttons:
                            for row in event.buttons:
                                for button in row:
                                    if hasattr(button, 'text'):
                                        for e in emojis:
                                            if e in button.text:
                                                console.print(f"[{session_name}] ✅ [green]Clicking {button.text}[/green]")
                                                await button.click()
                                                solved.set()
                                                return
                    console.print(f"[{session_name}] ❌ [red]No matching emoji found[/red]")
                except Exception as e:
                    console.print(f"[{session_name}] ❌ [red]Error solving captcha:[/red] {e}")
                finally:
                    if not solved.is_set():
                        solved.set()

            try:
                await asyncio.wait_for(solved.wait(), timeout=15)
            except asyncio.TimeoutError:
                console.print(f"[{session_name}] ⏳ [yellow]No captcha message received[/yellow]")

    except Exception as e:
        console.print(f"[{session_name}] ❌ [red]Error:[/red] {e}")

    finally:
        await client.disconnect()
        console.print(f"[{session_name}] 🎉 [green]Referral completed[/green]")

# ---------------- Referral (Math Captcha) ----------------
async def refer_with_math(session_name, api_id, api_hash, bot_link, wait_seconds=12):
    client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
    await client.start()
    try:
        m = re.match(r"https?://t\.me/([a-zA-Z0-9_]+)(\?start=(.*))?", bot_link)
        if not m:
            console.print(f"[{session_name}] ❌ [red]Invalid bot link[/red]")
            await client.disconnect()
            return
        bot_username = m.group(1)
        start_param = m.group(3) or ""

        if start_param:
            await client.send_message(bot_username, f"/start {start_param}")
        else:
            await client.send_message(bot_username, "/start")

        console.print(f"[{session_name}] ⏳ [yellow]Waiting for math captcha...[/yellow]")

        for _ in range(wait_seconds):
            await asyncio.sleep(1)
            msgs = await client.get_messages(bot_username, limit=1)
            if not msgs:
                continue
            msg = msgs[0]
            text = getattr(msg, "message", "") or ""
            match = re.search(r"(\d+)\s*([\+\-\*xX/÷])\s*(\d+)", text)
            if match:
                a, op, b = match.groups()
                try:
                    a_n, b_n = int(a), int(b)
                    if op in ("x", "X", "*"):
                        res = a_n * b_n
                    elif op in ("/", "÷"):
                        res = a_n // b_n if b_n != 0 else 0
                    elif op == "+":
                        res = a_n + b_n
                    elif op == "-":
                        res = a_n - b_n
                    else:
                        res = a_n + b_n
                    await client.send_message(bot_username, str(res))
                    console.print(f"[{session_name}] 🧮 [green]Answered: {res}[/green]")
                    return
                except Exception as e:
                    console.print(f"[{session_name}] ❌ [red]Failed compute:[/red] {e}")
                    return
        console.print(f"[{session_name}] ❌ [red]No math challenge received[/red]")
    except Exception as e:
        console.print(f"[{session_name}] ❌ [red]Error:[/red] {e}")
    await client.disconnect()

# ---------------- Join Channels ----------------
async def join_channels(accounts, channels, session_folder):
    for acc in accounts:
        session_name, api_id, api_hash = acc["session_name"], acc["api_id"], acc["api_hash"]
        client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
        await client.start()
        try:
            for channel in channels:
                ch = channel.strip().replace("https://t.me/", "").lstrip("@")
                try:
                    await client(JoinChannelRequest(ch))
                    console.print(f"[{session_name}] ✅ [green]Joined {ch}[/green]")
                except Exception as e:
                    console.print(f"[{session_name}] ❌ [red]Failed to join {ch}:[/red] {e}")
        except Exception as e:
            console.print(f"[{session_name}] ❌ [red]Error:[/red] {e}")
        finally:
            await client.disconnect()
            console.print(f"[{session_name}] 🎉 [cyan]Done joining[/cyan]")
            # ---------------- Leave Channels ----------------
async def leave_channels(session_name, api_id, api_hash):
    client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
    await client.start()
    try:
        limit = int(Prompt.ask("[yellow]How many groups/channels to leave?[/yellow]", default="10"))
    except:
        limit = 10

    dialogs = await client.get_dialogs()
    count = 0
    for dialog in dialogs:
        if getattr(dialog, "is_group", False) or getattr(dialog, "is_channel", False):
            try:
                await client.delete_dialog(dialog.id)
                count += 1
                console.print(f"[{session_name}] ✅ [green]Left {dialog.name}[/green]")
            except Exception as e:
                console.print(f"[{session_name}] ❌ [red]Failed to leave {dialog.name}:[/red] {e}")
            if count >= limit:
                break
    console.print(f"🎯 [cyan]Done. Left {count} groups/channels[/cyan].")
    await client.disconnect()

# ---------------- Manual Leave ----------------
async def manual_leave(session_name, api_id, api_hash):
    client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
    await client.start()
    try:
        links_input = Prompt.ask("[yellow]Enter channel links (comma separated)[/yellow]").strip()
        links = [x.strip() for x in links_input.split(",") if x.strip()]

        if not links:
            console.print("⚠️ [yellow]No valid links provided[/yellow]")
            await client.disconnect()
            return

        left_count = 0
        for link in links:
            try:
                entity = await client.get_entity(link)
                await client(LeaveChannelRequest(entity))
                console.print(f"[{session_name}] ✅ [green]Left {link}[/green]")
                left_count += 1
            except Exception as e:
                console.print(f"[{session_name}] ❌ [red]Failed to leave {link}:[/red] {e}")

        console.print(f"🎯 [cyan]Done. Left {left_count} groups/channels[/cyan].")
    finally:
        await client.disconnect()

# ---------------- Send Message ----------------
async def send_message_to_user(session_name, api_id, api_hash, username, message):
    client = TelegramClient(os.path.join(session_folder, session_name), api_id, api_hash)
    await client.start()
    try:
        await client.send_message(username, message)
        console.print(f"[{session_name}] ✅ [green]Message sent to {username}[/green]")
    except Exception as e:
        console.print(f"[{session_name}] ❌ [red]Failed to send message:[/red] {e}")
    await client.disconnect()

# ---------------- Main Menu ----------------
async def main_menu():
    show_banner()
    user = ensure_user_setup()

    ok = await generate_and_send_otp_if_needed(user)
    if not ok:
        console.print("❌ [red]OTP flow problem. Exiting...[/red]")
        return

    while True:
        table = Table(title="Main Menu", box=box.HEAVY, header_style="bold magenta")
        table.add_column("Option", justify="center", style="cyan", width=8)
        table.add_column("Description", style="bold white")
        table.add_row("1", "Manage Accounts")
        table.add_row("2", "Referral (No Captcha)")
        table.add_row("3", "Referral (Emoji Captcha)")
        table.add_row("4", "Referral (Math Captcha)")
        table.add_row("5", "Join Channels")
        table.add_row("6", "Auto Leave")
        table.add_row("7", "Send Message")
        table.add_row("8", "Update User Info / Re-login Owner")
        table.add_row("9", "Manual Leave")
        table.add_row("10", "Exit")
        console.print(table)

        choice = Prompt.ask("[bold yellow]Choose an option[/bold yellow]", choices=[str(i) for i in range(1, 11)])

        if choice == "1":
            await manage_accounts()

        elif choice in ["2", "3", "4"]:
            accounts = load_json(accounts_file) or []
            if not accounts:
                console.print("⚠ [yellow]No saved accounts. Add accounts first.[/yellow]")
                continue
            bot_link = Prompt.ask("[cyan]Enter Telegram bot referral link (https://t.me/...)[/cyan]")

            if choice == "2":
                for acc in accounts:
                    await refer_no_captcha(acc["session_name"], acc["api_id"], acc["api_hash"], bot_link)
            elif choice == "3":
                for acc in accounts:
                    await refer_with_emoji(acc["session_name"], acc["api_id"], acc["api_hash"], bot_link, True)
            elif choice == "4":
                for acc in accounts:
                    await refer_with_math(acc["session_name"], acc["api_id"], acc["api_hash"], bot_link)

        elif choice == "5":
            accounts = load_json(accounts_file) or []
            if not accounts:
                console.print("⚠ [yellow]No saved accounts[/yellow]")
                continue
            channels = Prompt.ask("[cyan]Enter channels (comma-separated)[/cyan]").split(",")
            await join_channels(accounts, channels, session_folder)

        elif choice == "6":
            accounts = load_json(accounts_file) or []
            if not accounts:
                console.print("⚠ [yellow]No saved accounts[/yellow]")
                continue
            for acc in accounts:
                await leave_channels(acc["session_name"], acc["api_id"], acc["api_hash"])

        elif choice == "7":
            accounts = load_json(accounts_file) or []
            if not accounts:
                console.print("⚠ [yellow]No saved accounts[/yellow]")
                continue
            username = Prompt.ask("[cyan]Enter username/bot/channel to send to[/cyan]")
            message = Prompt.ask("[cyan]Enter message to send[/cyan]")
            target = Prompt.ask("[cyan]Send from (account number / all)[/cyan]")

            if target.lower() == "all":
                for acc in accounts:
                    await send_message_to_user(acc["session_name"], acc["api_id"], acc["api_hash"], username, message)
            else:
                try:
                    idx = int(target) - 1
                    if 0 <= idx < len(accounts):
                        acc = accounts[idx]
                        await send_message_to_user(acc["session_name"], acc["api_id"], acc["api_hash"], username, message)
                    else:
                        console.print("❌ [red]Invalid account number[/red]")
                except Exception:
                    console.print("❌ [red]Invalid input[/red]")

        elif choice == "8":
            user = ensure_user_setup()
            console.print(Panel("=== Update User Info ===", style="cyan"))
            new_id = Prompt.ask("Telegram ID", default=user.get("id", ""))
            new_username = Prompt.ask("Username", default=user.get("username", ""))
            user['id'] = sanitize_user_id(new_id)
            user['username'] = new_username
            user['otp_verified'] = False
            save_json(user_file, user)
            console.print("✅ [green]User info updated[/green]")

        elif choice == "9":
            accounts = load_json(accounts_file) or []
            if not accounts:
                console.print("⚠ [yellow]No saved accounts[/yellow]")
                continue
            for acc in accounts:
                await manual_leave(acc["session_name"], acc["api_id"], acc["api_hash"])

        elif choice == "10":
            console.print("👋 [cyan]Exiting...[/cyan]")
            break

# ---------------- Entry ----------------
if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        console.print("\n👋 [cyan]Exited by user[/cyan]")