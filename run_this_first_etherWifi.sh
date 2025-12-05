# 1) Remove Ethernet as default
sudo ip route del default dev eth0 || true

# 2) Add Wi-Fi as default with higher priority
sudo ip route add default via 172.20.10.1 dev wlan0 metric 50 || \
sudo ip route replace default via 172.20.10.1 dev wlan0 metric 50

# 3) Verify and test
ip route show
ping -c 3 172.20.10.1
ping -c 3 8.8.8.8