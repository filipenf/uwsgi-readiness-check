import time


def application(_, s):
    print("[Python App] sleeping")
    time.sleep(3)
    s('200 OK', [('Content-Type', 'text/html')])
    return [b"OK"]
