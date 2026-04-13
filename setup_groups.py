"""One-shot script: create the 5 bridge groups and print gateways config JSON.

Run before deploying the bot:
  docker run --rm \
    -e DC_EMAIL=deltachat@h4ks.com -e DC_PASSWORD=<password> \
    -v /data/matterdelta:/data \
    <image> python3 /setup_groups.py

Outputs the gateways array to paste into config.json, plus invite links.
"""

import json
import os
import subprocess
import sys
import time

CHANNELS = ["lobby", "bots", "minecraft", "news", "buddhism"]
DATA_DIR = os.environ.get("DATA_DIR", "/data")
DC_EMAIL = os.environ["DC_EMAIL"]
DC_PASSWORD = os.environ["DC_PASSWORD"]

env = os.environ.copy()
env["DC_ACCOUNTS_PATH"] = os.path.join(DATA_DIR, "accounts")
os.makedirs(env["DC_ACCOUNTS_PATH"], exist_ok=True)

proc = subprocess.Popen(
    ["deltachat-rpc-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    env=env,
)

_id = 0


def call(method, *args):
    global _id
    _id += 1
    req = json.dumps({"jsonrpc": "2.0", "method": method, "params": list(args), "id": _id}) + "\n"
    proc.stdin.write(req.encode())
    proc.stdin.flush()
    r = json.loads(proc.stdout.readline())
    if "error" in r:
        print(f"RPC error on {method}: {r['error']}", file=sys.stderr)
        return None
    return r["result"]


# Get or create account
accounts = call("get_all_account_ids")
if accounts:
    accid = accounts[0]
    print(f"Using existing account id={accid}", file=sys.stderr)
else:
    accid = call("add_account")
    print(f"Created account id={accid}", file=sys.stderr)
    call("set_config", accid, "addr", DC_EMAIL)
    call("set_config", accid, "mail_pw", DC_PASSWORD)
    print("Configured IMAP credentials", file=sys.stderr)

# Configure account (connects to IMAP, generates OpenPGP key)
if not call("is_configured", accid):
    print("Configuring account (connecting to IMAP)...", file=sys.stderr)
    call("configure", accid)
    # Wait for configure to complete — polls up to 60s
    for _ in range(60):
        time.sleep(1)
        if call("is_configured", accid):
            break
    else:
        print("ERROR: account failed to configure after 60s", file=sys.stderr)
        proc.terminate()
        sys.exit(1)
    print("Account configured.", file=sys.stderr)

call("start_io", accid)
time.sleep(2)

gateways = []
print("\n=== Delta Chat invite links ===\n", file=sys.stderr)

for channel in CHANNELS:
    group_name = f"h4ks {channel}"

    chat_id = call("create_group_chat", accid, group_name, False)
    print(f"{channel}: created group chatId={chat_id}", file=sys.stderr)

    invite_url = call("get_chat_securejoin_qr_code", accid, chat_id) or ""
    print(f"  invite: {invite_url}", file=sys.stderr)

    gateways.append({"gateway": channel, "accountId": accid, "chatId": chat_id})

proc.terminate()

print(json.dumps(gateways, indent=2))
