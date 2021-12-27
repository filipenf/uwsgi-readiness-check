# Uses 6 threads to generate requests and force uwsgi
# queuing to happen

import requests
import threading


def request_loop():
    while True:
        requests.get('http://uwsgi-test:8080/')


if __name__ == "__main__":
    threads = []
    for i in range(20):
        t = threading.Thread(target=request_loop)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
