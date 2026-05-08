#!/bin/sh
set -e

mkdir -p /opt/rdgen/exe /opt/rdgen/png /opt/rdgen/temp_zips
chown -R user:user /opt/rdgen/exe /opt/rdgen/png /opt/rdgen/temp_zips

exec su-exec user "$@"
