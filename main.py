import wifi
import os
import adafruit_requests
import socketpool
import ssl

ignore = [
	"/lib",
	"/main.py",
	"/boot.py",
]

wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
pool = socketpool.SocketPool(wifi.radio)
context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, context)

print("*" * 80)
print("*" * 80)
print("*" * 80)

import ugit
ugitter = ugit.UGit(requests, user="Neradoc", repository="ugit_test", ignore=ignore)
ugitter.pull_all()
