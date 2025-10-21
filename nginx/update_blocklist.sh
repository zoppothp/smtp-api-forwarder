#!/bin/sh

LOG_FILE=/var/log/nginx/access.log
BLOCKLIST=/etc/nginx/conf.d/blocklist.conf
TIME_WINDOW="1 hour ago"

# Parse logs for IPs with more than 3 requests in the last hour
awk -v time_window="$TIME_WINDOW" '
    $4 > "['\"`date -d "$time_window" +"%d/%b/%Y:%H:%M:%S"`'\"]" {
        ip_count[$1]++
    }
    END {
        for (ip in ip_count) {
            if (ip_count[ip] > 3) {
                print "deny " ip ";"
            }
        }
    }
' $LOG_FILE > $BLOCKLIST.tmp

# Overwrite the blocklist (mounted volume)
cat $BLOCKLIST.tmp > $BLOCKLIST
rm $BLOCKLIST.tmp

# Reload Nginx
nginx -s reload
