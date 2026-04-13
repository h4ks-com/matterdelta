#!/bin/sh
set -e

CFG=/data

# Only configure on first run — skip if account already exists.
# matterdelta init/config are broken on newer deltabot-cli (Bot has no configure
# method), so we use the rpc-server directly for fresh setups.
ACCTS="$CFG/accounts"
if [ ! -d "$ACCTS" ] || [ -z "$(ls -A "$ACCTS" 2>/dev/null)" ]; then
    echo "No existing account found — running initial setup via rpc-server..."
    python3 /init_account.py
fi

matterdelta --config-dir "$CFG" serve
