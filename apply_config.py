"""Apply DC account config settings on every container start.

Runs before matterdelta serve to ensure settings like delete_device_after
are always correct, regardless of whether init_account.py ran.
"""

import json
import os
import subprocess
import sys
import time

DATA_DIR = os.environ.get("DATA_DIR", "/data")

env = os.environ.copy()
env["DC_ACCOUNTS_PATH"] = os.path.join(DATA_DIR, "accounts")

_id = 0
proc = None


def start_proc():
    global proc, _id
    if proc is not None:
        try:
            proc.terminate()
        except OSError:
            pass
    _id = 0
    proc = subprocess.Popen(
        ["deltachat-rpc-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env,
    )


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


start_proc()

# rpc-server may take a moment to initialize accounts — retry, respawning if pipe breaks
for attempt in range(20):
    try:
        accounts = call("get_all_account_ids")
        break
    except (json.JSONDecodeError, ValueError):
        time.sleep(0.5)
    except (BrokenPipeError, OSError):
        time.sleep(0.5)
        start_proc()
else:
    print("ERROR: rpc-server did not become ready in time", file=sys.stderr)
    proc.terminate()
    sys.exit(1)

if not accounts:
    print("No accounts found, skipping config apply.", file=sys.stderr)
    proc.terminate()
    sys.exit(0)

accid = accounts[0]

call("set_config", accid, "delete_device_after", "172800")
print(f"Applied config for account {accid}: delete_device_after=172800", file=sys.stderr)

proc.terminate()
