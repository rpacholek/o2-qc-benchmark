import signal
import time
import sys

def wait_until_kill(f):
    def sig_handler(signum, frame):
        print(f"Signal {signum}")
        f()
        sys.exit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    while True:
        time.sleep(10000)

