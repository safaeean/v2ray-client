#!/bin/bash

SOCKS_PORT=${1:-1080}

# 1. پاکسازی تنظیمات قبلی
sudo ip link delete tun0 2>/dev/null
sudo ip route flush table 100 2>/dev/null
sudo ip rule del fwmark 1 2>/dev/null
sudo iptables -t mangle -F
sudo iptables -t nat -F

# 2. ایجاد tun0
sudo ip tuntap add dev tun0 mode tun
sudo ip addr add 10.0.0.2/24 dev tun0
sudo ip link set tun0 up
sudo ip link set dev tun0 mtu 1500

# 3. تنظیم DNS (مهم!)
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf >/dev/null
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf >/dev/null

# 4. تنظیم routing پیشرفته
sudo ip route add default via 10.0.0.1 dev tun0 table 100
sudo ip rule add fwmark 1 lookup 100

# 5. تنظیمات iptables دقیق
# معاف کردن ترافیک به سمت پروکسی
sudo iptables -t mangle -A OUTPUT -d 127.0.0.1 -p tcp --dport $SOCKS_PORT -j RETURN

# مارک گذاری سایر ترافیک
sudo iptables -t mangle -A OUTPUT -p tcp -j MARK --set-mark 1
sudo iptables -t mangle -A OUTPUT -p udp -j MARK --set-mark 1

# NAT
sudo iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE

# 6. اجرای tun2socks با پارامترهای بهینه
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo "$SCRIPT_DIR/../bin/tun2socks" \
  -device tun0 \
  -proxy "socks5://127.0.0.1:$SOCKS_PORT" \
  -loglevel debug \
  -udp-timeout 30s \
  -tcp-rcvbuf 2097152 \
  -tcp-sndbuf 2097152 &

# 7. غیرفعال کردن IPv6 (اختیاری)
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1

echo "Tun2socks started successfully! Testing connectivity..."
sleep 3

# 8. تست خودکار
echo "Testing DNS resolution..."
dig google.com +short +time=1 +tries=1

echo "Testing HTTP through tun0..."
curl --interface tun0 --connect-timeout 5 -v http://example.com