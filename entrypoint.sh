#!/bin/sh
set -e

CFG=/data

# On first run (no account yet), configure the account via rpc-server.
# matterdelta init/config are broken on newer deltabot-cli (Bot has no
# configure method), so we talk to deltachat-rpc-server directly.
ACCTS="$CFG/accounts"
if [ ! -d "$ACCTS" ] || [ -z "$(ls -A "$ACCTS" 2>/dev/null)" ]; then
    echo "No existing account found — running initial setup via rpc-server..."
    python3 /init_account.py
fi

# Always apply runtime config via rpc-server before starting serve.
# This ensures settings like delete_device_after survive container rebuilds.
python3 /apply_config.py

matterdelta --config-dir "$CFG" serve
