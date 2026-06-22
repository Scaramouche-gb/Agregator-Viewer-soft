"""
viev.py - Telegram post views inflation utility
- run_account_lifecycle: Individual account lifecycle execution
- main: Scanning sessions, configuration validation and concurrent start
"""

import asyncio
import os
import sys
import json
import random
import shutil
import socket
import subprocess
import time
from datetime import datetime, timedelta
from typing import Optional

from hydrogram.raw.types import Message
from hydrogram.raw.all import objects
objects[0x95ef6f2b] = Message



CONFIG_FILE = 'config.json'
SESSIONS_DIR = 'sessions'



class GostTunnel:
    """Local tunnel manager using gost for HTTP/HTTPS proxies"""

    def __init__(self, proxy_url: str):
        self.proxy_url = proxy_url
        self.process: Optional[subprocess.Popen] = None
        self.local_port: Optional[int] = None

    async def start(self) -> Optional[dict]:
        is_socks = self.proxy_url.startswith("socks5://") or self.proxy_url.startswith("socks4://")
        if is_socks:
            return parse_proxy_url(self.proxy_url)

        if not shutil.which("gost"):
            print("[X] Error: 'gost' utility not found in system! HTTP proxy cannot be started.")
            return None

        self.local_port = get_free_port()
        try:
            self.process = subprocess.Popen(
                ["gost", "-L", f"socks5://127.0.0.1:{self.local_port}", "-F", self.proxy_url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
            )
            
            for _ in range(50):
                if self.process.poll() is not None:
                    print("[X] Gost process terminated unexpectedly.")
                    return None
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.1)
                        if s.connect_ex(("127.0.0.1", self.local_port)) == 0:
                            return {
                                "scheme": "socks5",
                                "hostname": "127.0.0.1",
                                "port": self.local_port
                            }
                except:
                    pass
                await asyncio.sleep(0.1)
            
            print("[X] Timeout waiting for gost tunnel port.")
            return None
        except Exception as e:
            print(f"[X] Error starting gost: {e}")
            return None

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.process = None
                self.local_port = None



def normalize_proxy_url(proxy_url: str) -> str:
    """Normalizes proxy to scheme://user:pass@host:port format"""
    if not proxy_url:
        return ""
    proxy_url = proxy_url.strip()
    
    prefix = ""
    for p in ["socks5://", "socks4://", "http://", "https://"]:
        if proxy_url.lower().startswith(p):
            prefix = p
            proxy_url = proxy_url[len(p):]
            break
            
    if not prefix:
        prefix = "http://"
        
    proxy_url = proxy_url.rstrip("/")
    
    parts = proxy_url.split(":")
    if len(parts) == 4:
        ip, port, user, password = parts
        return f"{prefix}{user}:{password}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        return f"{prefix}{ip}:{port}"
    elif len(parts) == 3:
        user, pass_ip, port = parts
        if "@" in pass_ip:
            password, ip = pass_ip.split("@", 1)
            return f"{prefix}{user}:{password}@{ip}:{port}"
            
    return f"{prefix}{proxy_url}"



def parse_proxy_url(proxy_url: str) -> Optional[dict]:
    """Parses proxy URL into a dictionary for Hydrogram"""
    if not proxy_url:
        return None
    try:
        proxy_url = normalize_proxy_url(proxy_url)
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)
        scheme = parsed.scheme or "http"
        
        default_ports = {"http": 80, "https": 443, "socks5": 1080, "socks4": 1080}
        port = parsed.port or default_ports.get(scheme, 80)
        
        hostname = parsed.hostname
        username = parsed.username
        password = parsed.password
        
        return {
            "scheme": scheme,
            "hostname": hostname,
            "port": port,
            "username": username,
            "password": password
        }
    except Exception as e:
        print(f"[ERROR] Proxy parsing error {proxy_url}: {e}")
        return None



def get_free_port() -> int:
    """Finds a free local port for tunneling"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]



async def run_account_lifecycle(session_path: str, account_config: dict, global_config: dict):
    """Individual account lifecycle execution on Hydrogram"""
    acc_name = os.path.basename(session_path).replace('.session', '')
    
    while True:
        print(f"\n[!] [{acc_name}] Woke up. Starting activity session...")
        
        proxy_url = account_config.get("proxy_url")
        device_name = account_config.get("device_name", "Hydrogram-PC")
        
        tunnel = None
        proxy_settings = None
        
        if proxy_url:
            tunnel = GostTunnel(proxy_url)
            proxy_settings = await tunnel.start()
            if not proxy_settings:
                print(f"[X] [{acc_name}] Failed to start proxy tunnel. Sleeping until next cycle.")
                wait_seconds = random.randint(
                    int(global_config.get("read_interval_min", 7200)),
                    int(global_config.get("read_interval_max", 21600))
                )
                next_run = datetime.now() + timedelta(seconds=wait_seconds)
                print(f"--- [{acc_name}] Going to sleep. Next run: {next_run.strftime('%H:%M:%S')}")
                await asyncio.sleep(wait_seconds)
                continue
        
        client = None
        try:
            from hydrogram import Client
            from hydrogram.errors import FloodWait
            from hydrogram.raw import functions

            client = Client(
                name=acc_name,
                api_id=int(global_config["api_id"]),
                api_hash=global_config["api_hash"],
                workdir=os.path.dirname(session_path),
                proxy=proxy_settings,
                device_model=device_name,
                system_version="Linux 6.x",
                sleep_threshold=60
            )

            await asyncio.sleep(random.uniform(0.5, 2.0))
            await client.connect()
            try:
                me = await client.get_me()
                if not me:
                    print(f"[!] [{acc_name}] Error: Not authorized. Account skipped.")
                    return
            except Exception:
                print(f"[!] [{acc_name}] Error: Not authorized. Account skipped.")
                return 

            count = 0
            async for _ in client.get_dialogs(limit=5):
                count += 1
            await asyncio.sleep(random.uniform(3, 7))

            channel_identifiers = global_config.get("channel_identifier")
            if not isinstance(channel_identifiers, list):
                channel_identifiers = [channel_identifiers]

            async def process_channel(channel_id):
                try:
                    if isinstance(channel_id, str) and channel_id.startswith('-100'):
                        chat_id = int(channel_id)
                    else:
                        chat_id = channel_id
                except ValueError:
                    chat_id = channel_id

                chat = None
                try:
                    chat = await client.get_chat(chat_id)
                except Exception as e:
                    if "PEER_ID_INVALID" in str(e):
                        print(f"[!] [{acc_name}] Channel is unknown to session cache. Trying to resolve from dialogs...")
                        found = False
                        async for dialog in client.get_dialogs(limit=100):
                            if dialog.chat.id == chat_id or dialog.chat.username == chat_id:
                                chat = dialog.chat
                                found = True
                                break
                        if not found:
                            print(f"[X] [{acc_name}] Channel not found in latest dialogs.")
                    else:
                        print(f"[X] [{acc_name}] Error resolving channel {chat_id}: {e}")

                if not chat:
                    print(f"[X] [{acc_name}] Skipping channel {chat_id} due to access error.")
                    return

                check_limit = int(global_config.get("check_limit", 60))
                messages_ids = []
                async for message in client.get_chat_history(chat.id, limit=check_limit):
                    if message.id:
                        messages_ids.append(message.id)

                if not messages_ids:
                    print(f"[i] [{acc_name}] No posts found in channel {chat.title or chat_id}.")
                    return

                random.shuffle(messages_ids)
                target_peer = await client.resolve_peer(chat.id)

                for i in range(0, len(messages_ids), random.randint(2, 5)):
                    chunk = messages_ids[i:i + 5]
                    if not chunk:
                        continue

                    try:
                        await client.get_messages(chat.id, chunk)
                        await asyncio.sleep(random.uniform(1, 2))

                        await client.invoke(
                            functions.messages.GetMessagesViews(
                                peer=target_peer,
                                id=chunk,
                                increment=True
                            )
                        )
                        await client.read_chat_history(chat.id, max_id=max(chunk))
                    except Exception as e:
                        print(f"[X] [{acc_name}] Error viewing chunk in channel {chat.title or chat_id}: {e}")
                        break

                    delay = random.uniform(15, 45)
                    print(f"    [{acc_name}] [{chat.title or chat_id}] Reading chunk of posts... sleeping {delay:.1f} sec.")
                    await asyncio.sleep(delay)

                print(f"[V] [{acc_name}] Channel {chat.title or chat_id} processing complete.")

            await asyncio.gather(*(process_channel(cid) for cid in channel_identifiers))

        except FloodWait as e:
            print(f"[X] [{acc_name}] Flood wait error: waiting {e.value} seconds.")
        except Exception as e:
            print(f"[X] [{acc_name}] Error: {e}")
        finally:
            if client:
                try:
                    if client.is_connected:
                        await client.disconnect()
                except Exception as e_dis:
                    print(f"[X] [{acc_name}] Error during client disconnect: {e_dis}")
            if tunnel:
                tunnel.stop()

        wait_seconds = random.randint(
            int(global_config.get("read_interval_min", 7200)),
            int(global_config.get("read_interval_max", 21600))
        )
        next_run = datetime.now() + timedelta(seconds=wait_seconds)
        
        print(f"--- [{acc_name}] Going to sleep. Next run: {next_run.strftime('%H:%M:%S')}")
        await asyncio.sleep(wait_seconds)



async def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"Config file {CONFIG_FILE} not found!")
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            global_config = json.load(f)
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        return

    if not os.path.exists(SESSIONS_DIR):
        print(f"Sessions folder '{SESSIONS_DIR}' not found!")
        return

    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    if not session_files:
        print("No .session files found in sessions folder!")
        return

    active_accounts = []
    configured_accounts = {acc.get("name"): acc for acc in global_config.get("accounts", []) if acc.get("name")}

    for session_file in session_files:
        acc_name = session_file.replace('.session', '')
        if acc_name in configured_accounts:
            full_path = os.path.join(SESSIONS_DIR, session_file)
            active_accounts.append((full_path, configured_accounts[acc_name]))
        else:
            print(f"[i] Skipping session {session_file} as it is not present in {CONFIG_FILE}.")

    if not active_accounts:
        print("No accounts ready to start (all sessions missing from config.json)!")
        return

    print(f"--- SYSTEM LAUNCH: {len(active_accounts)} configured accounts ---")

    tasks = []
    for full_path, account_config in active_accounts:
        initial_delay = random.randint(60, 7200)
        acc_name = os.path.basename(full_path).replace('.session', '')

        async def delayed_start(path, acc_conf, delay):
            name = os.path.basename(path).replace('.session', '')
            print(f"[i] {name} will start in {delay // 60} min.")
            await asyncio.sleep(delay)
            await run_account_lifecycle(path, acc_conf, global_config)

        tasks.append(delayed_start(full_path, account_config, initial_delay))

    await asyncio.gather(*tasks)



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSystem stopped.")
