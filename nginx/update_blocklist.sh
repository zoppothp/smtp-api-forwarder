#!/bin/sh

LOG_FILE=/var/log/nginx/access.log
BLOCKLIST=/etc/nginx/conf.d/blocklist.conf

# Find IPs with more than 3 requests in the last hour
awk -v d1="$(date --date='1 hour ago' '+%d/%b/%Y:%H:%M:%S')" \
    -v d2="$(date '+%d/%b/%Y:%H:%M:%S')" \
    '$0 > d1 && $0 < d2 {print $1}' $LOG_FILE | \
    sort | uniq -c | \
    awk '$1 > 3 {print "deny " $2 ";"}' > $BLOCKLIST.tmp

# Reload Nginx if blocklist changed
if ! diff -q $BLOCKLIST $BLOCKLIST.tmp > /dev/null 2>&1; then
    mv $BLOCKLIST.tmp $BLOCKLIST
    nginx -s reload
fi
