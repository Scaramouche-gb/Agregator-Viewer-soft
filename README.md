# Agregator-Viewer-soft

A high-performance, asynchronous Telegram post views inflation utility built on top of the **Hydrogram** library. 

This tool is designed to work in synergy with **ShadowGram**. You can easily warm up your accounts in ShadowGram, then copy the session files and configuration objects directly here.

---

## Key Features

* **Hydrogram Engine**: Active, modern, and fast asynchronous client wrapper for the Telegram MTProto API.
* **ShadowGram Integration**: Native compatibility with ShadowGram's account configuration format. Just copy and paste account entries straight from your ShadowGram configuration.
* **Gost Tunneling**: Automatic HTTP/HTTPS proxy tunnel initialization using the `gost` utility. Tunnel processes are spawned dynamically when the account wakes up and are terminated immediately upon going to sleep to save system resources.
* **Direct SOCKS Support**: Direct connection support for SOCKS5 and SOCKS4 proxies without running external utilities.
* **Account Device Fingerprints**: Individual device names (`device_model`) applied to each client connection to avoid bot detection.
* **Safe Mode**: Any `.session` file placed in the `sessions/` directory is **automatically ignored** if it is not configured in `config.json` to prevent accidental execution from your native/home IP.
* **Human-like Behavior**: Shuffled chunk-based post viewing, random reading delays (15–45 seconds), and customized activity/sleep intervals (2–6 hours).

---

## Requirements

1. **Python 3.8+**
2. Install dependencies:
   ```bash
   pip install hydrogram
   ```
3. **Gost** (only required if you use HTTP/HTTPS proxies):
   Make sure the `gost` binary is installed and available in your system's `PATH`.

---

## Configuration (`config.json`)

Create a `config.json` file in the root directory. You can copy the API credentials and accounts straight from your ShadowGram configuration:

```json
{
  "api_id": 34183260,
  "api_hash": "b1d8c616e1295b671f1e43c22ede5cf2",
  "channel_identifier": "@my_aggregator_channel",
  "read_interval_min": 7200,
  "read_interval_max": 21600,
  "check_limit": 60,
  "accounts": [
    {
      "name": "acc1",
      "proxy_url": "http://user:pass@192.168.1.1:8000",
      "device_name": "Razer-Blade-14-L4DY"
    }
  ]
}
```

### Configuration Fields

* `api_id` / `api_hash`: Your Telegram API keys.
* `channel_identifier`: Username (e.g., `@my_channel`) or channel ID (e.g., `-100123456789`) to view posts.
* `read_interval_min` / `read_interval_max`: Range of seconds an account sleeps between activity sessions (default: 2 to 6 hours).
* `check_limit`: Number of latest posts to retrieve and view (default: 60).
* `accounts`: List of account configurations. You only need the `name` (matching your `.session` filename), `proxy_url` (optional), and `device_name` (optional) keys. Any extra keys copied from ShadowGram configuration are ignored.

---

## Setup & Workflow

1. **Configure ShadowGram**: Create and warm up your accounts. Set up proxies and device names.
2. **Export Sessions**: Copy the `.session` file (e.g., `account.session` from ShadowGram's account directory) into the `sessions/` folder of this utility and rename it to match your account name (e.g., `acc1.session`).
3. **Update Config**: Copy the corresponding account object from ShadowGram's config file and paste it into the `accounts` array in `config.json`.
4. **Run the Script**:
   ```bash
   python "viev.py"
   ```
5. **Add New Accounts**: Simply drop another session file into `sessions/`, add its proxy and device info to `config.json`, and restart the script.

---

## Spacing and Code Style

This code follows the **Nachzehrer** formatting guidelines:
* Global scope functions, class definitions, and the launch block are separated by exactly **3 empty lines**.
* Minimal internal comments inside the code for maximum readability and clean appearance.