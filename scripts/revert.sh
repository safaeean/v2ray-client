# حذف TUN interface
sudo ip link delete tun0 2>/dev/null

# بازگرداندن routing اصلی
sudo ip route flush table 100
sudo ip rule del fwmark 1 table 100 2>/dev/null

# بازگرداندن تنظیمات iptables
sudo iptables -t mangle -F
sudo iptables -t nat -F


# ریست کردن network manager
sudo systemctl restart NetworkManager