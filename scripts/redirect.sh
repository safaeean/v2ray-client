#!/bin/bash

SOCKS_PORT=$1
if [ -z "$SOCKS_PORT" ]; then
    echo "Usage: $0 <SOCKS_PORT>"
    exit 1
fi

# حذف tun0 اگر وجود داشته باشد
if ip link show tun0 > /dev/null 2>&1; then
    ip link delete tun0
fi

# ساخت TUN interface
ip tuntap add dev tun0 mode tun || exit 1
ip addr add 10.0.0.2/24 dev tun0
ip link set tun0 up

# ساخت جدول روتینگ
ip rule add fwmark 1 table 100 2>/dev/null
ip route add default dev tun0 table 100 2>/dev/null

# ساخت chain فقط در صورت نیاز
if ! iptables -t mangle -L DIVERT &>/dev/null; then
    iptables -t mangle -N DIVERT
    iptables -t mangle -A PREROUTING -p tcp -m socket -j DIVERT
    iptables -t mangle -A DIVERT -j MARK --set-mark 1
    iptables -t mangle -A DIVERT -j ACCEPT
fi

# اجرای tun2socks
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/../bin/tun2socks" -device tun0 -proxyServer socks5://127.0.0.1:$SOCKS_PORT -interface tun0 &
echo "Ok !"