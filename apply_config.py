"""Apply DC account config settings on every container start.

Runs before matterdelta serve to ensure settings like delete_device_after
are always correct, regardless of whether init_account.py ran.
"""

import json
import os
import subprocess
import sys

DATA_DIR = os.environ.get("DATA_DIR", "/data")

env = os.environ.copy()
env["DC_ACCOUNTS_PATH"] = os.path.join(DATA_DIR, "accounts")

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
if not accounts:
    print("No accounts found, skipping config apply.", file=sys.stderr)
    proc.terminate()
    sys.exit(0)

accid = accounts[0]

# 2-day message cleanup on the bot device
call("set_config", accid, "delete_device_after", "172800")
print(f"Applied config for account {accid}: delete_device_after=172800", file=sys.stderr)

proc.terminate()
