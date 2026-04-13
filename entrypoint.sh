#!/bin/sh
set -e

CFG=/data

matterdelta --config-dir "$CFG" init "$DC_EMAIL" "$DC_PASSWORD"
matterdelta --config-dir "$CFG" config delete_device_after 172800
matterdelta --config-dir "$CFG" serve
