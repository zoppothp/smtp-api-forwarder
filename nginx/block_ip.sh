#!/bin/sh
IP=$1
BLOCKLIST=/etc/nginx/conf.d/blocklist.conf

# Add IP to blocklist if not already present
if ! grep -q "deny $IP;" $BLOCKLIST; then
    echo "deny $IP;" >> $BLOCKLIST
    nginx -s reload
fi
