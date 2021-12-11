import time
import sys
import atexit

def application(e, s):
    print("[Python App] sleeping")
    time.sleep(3)
    s('200 OK', [('Content-Type', 'text/html')])
    return [b"OK"]
