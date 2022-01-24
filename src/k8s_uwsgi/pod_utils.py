#!/usr/bin/env python3
# Utilities for pod lifecycle management
# Graceful shutdown: Called by the kubernetes preStop hook:
#  1. Creates a "shutdown file" which fails readiness checks and tells k8s
#     to stop sending more traffic to the pod.
#  2. Monitors the uwsgi stats socket for in-flight connections, allowing
#     k8s to kill the pod once it is drained
#
# Readiness check:
#  The readiness check fails if:
#  1. Shutdown file exists
#  2. uwsgi-stats reports queue size greater than 30% of its max size
#  3. the uwsgi-stats socket is not present (meaning uwsgi is dead)

import json
import logging
import socket
import os
import time
from datetime import datetime

BUFF_SIZE = 8192
UWSGI_STATS_SOCKET = "/tmp/uwsgi_stats.socket"
UWSGI_MASTER_FIFO = "/tmp/uwsgi-fifo"
DEFAULT_SHUTDOWN_PROGRESS_FILE = "/tmp/uwsgi-shutdown-progress"
DEFAULT_SHUTDOWN_TIMEOUT = 60


def read_uwsgi_socket(stats_socket):
    # 1 check if the socket file exists (indicates that uwsgi is not running)
    if not os.path.exists(stats_socket):
        logging.fatal("Unable to connect to the uwsgi stats socket")
        exit(1)

    # 2 connect to the socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(stats_socket)
    except ConnectionRefusedError:
        logging.fatal("Connection refused: uwsgi process is not responding")
        exit(1)

    # 3 loads json from the socket
    data = b""
    while True:
        msg = sock.recv(BUFF_SIZE)
        data += msg
        if len(msg) < BUFF_SIZE:
            break

    return json.loads(data.decode("utf-8"))


def requests_in_flight(stats_socket):
    """
    Returns the number of requests being processed + queued
    """
    stats = read_uwsgi_socket(stats_socket)
    queued = int(stats["sockets"][0]["queue"])
    return (
        sum(
            [
                core.get("in_request", 0)
                for worker in stats["workers"]
                for core in worker["cores"]
            ]
        )
        + queued
    )


def graceful_shutdown(stats_socket, shutdown_file, max_wait, uwsgi_fifo=None):
    """
    Creates the SHUTDOWN_START_FILE which will cause readiness checks to
    fail. Then waits until all workers have finished processing their requests
    and listen queue is drained.
    After drained, creates the SHUTDOWN_COMPLETE_FILE which is used by the
    haproxy sidecar to complete its termination
    """

    def shutdown_log(message):
        with open(shutdown_file) as f:
            f.write(
                "{}: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)
            )

    # Creates the shutdown file so readiness checks fail
    logging.info("Pod shutdown started")
    shutdown_log("Shutdown started")
    wait = max_wait
    in_flight = requests_in_flight(stats_socket)
    while wait > 0 and in_flight > 0:
        wait = wait - 1
        logging.info(
            "{} requests in flight. Delaying shutdown ({})".format(in_flight, wait)
        )
        time.sleep(1)
        in_flight = requests_in_flight(stats_socket)

    logging.info("Graceful shutdown finished with %d seconds left", wait)
    shutdown_log("Shutdown complete")

    if uwsgi_fifo is not None:
        with open(UWSGI_MASTER_FIFO, "w") as fifo:
            fifo.write("q")
            fifo.flush()

    return wait


def check_ready(stats_socket, queue_threshold, shutdown_file):
    shutdown_in_progress = os.path.isfile(shutdown_file)

    stats = read_uwsgi_socket(stats_socket)
    # check and compare queue size
    try:
        queue = int(stats["sockets"][0]["queue"])
        max_queue = int(os.environ.get("UWSGI_LISTEN", -1))
        if max_queue == -1:
            max_queue = int(stats["sockets"][0]["max_queue"])
        queue_limit = max_queue * float(queue_threshold)
        if shutdown_in_progress:
            logging.warning(
                "Not ready: Shutdown in progress. Queued requests: %d | Limit = %d",
                queue,
                queue_limit,
            )
            return False

        if queue > queue_limit:
            logging.warning(
                "Not ready: Queued requests: %d | Limit = %d", queue, queue_limit
            )
            return False
        else:
            logging.warning(
                "Ready: Queued requests: %d | Limit = %d", queue, queue_limit
            )
            return True
    except (KeyError, IndexError, TypeError) as e:
        logging.fatal("Error loading uwsgi stats data. Error: {}".format(str(e)))
        exit(1)
