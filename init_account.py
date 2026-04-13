"""Configure a fresh Delta Chat account via deltachat-rpc-server.

Called by entrypoint.sh on first run when no account exists yet.
Reads DC_EMAIL and DC_PASSWORD from environment.
"""

import json
import os
import subprocess
import sys
import time

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


accounts = call("get_all_account_ids")
if accounts:
    accid = accounts[0]
    print(f"Using existing account id={accid}", file=sys.stderr)
else:
    accid = call("add_account")
    print(f"Created account id={accid}", file=sys.stderr)
    call("set_config", accid, "addr", DC_EMAIL)
    call("set_config", accid, "mail_pw", DC_PASSWORD)

if not call("is_configured", accid):
    print("Configuring account (connecting to IMAP)...", file=sys.stderr)
    call("configure", accid)
    for _ in range(60):
        time.sleep(1)
        if call("is_configured", accid):
            break
    else:
        print("ERROR: account failed to configure after 60s", file=sys.stderr)
        proc.terminate()
        sys.exit(1)
    print("Account configured.", file=sys.stderr)
else:
    print("Account already configured.", file=sys.stderr)

# 2-day message cleanup on the bot device
call("set_config", accid, "delete_device_after", "172800")
print("Set delete_device_after=172800", file=sys.stderr)

proc.terminate()
