import argparse

from k8s_uwsgi.pod_utils import graceful_shutdown
from k8s_uwsgi.pod_utils import check_ready
from k8s_uwsgi.pod_utils import DEFAULT_SHUTDOWN_PROGRESS_FILE


def shutdown():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", default=False, action="store_true")
    parser.add_argument("--uwsgi-stats-socket")
    parser.add_argument("--uwsgi-master-fifo")
    parser.add_argument(
        "--max-attempts",
        help="How many cycles to wait for the queue to drain before forcefully killing uwsgi",
    )
    parser.add_argument(
        "--shutdown-progress-file",
        default=DEFAULT_SHUTDOWN_PROGRESS_FILE,
        help="If this file exists, readiness checks will fail",
    )

    args = parser.parse_args()

    if (
        graceful_shutdown(
            args.uwsg_stats_socket,
            args.shutdown_progress_file,
            args.max_wait,
            args.uwsgi_master_fifo,
        )
        < 1
    ):
        exit(-1)


def is_ready():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", default=False, action="store_true")
    parser.add_argument("--stats-socket", default="/tmp/uwsgi-stats.socket")
    parser.add_argument(
        "--queue-threshold",
        help="uwsgi queue threshold (a value between 0 and 1). Default: 0.5",
        type=float,
        default=0.5,
    )
    parser.add_argument(
        "--shutdown-progress-file",
        default=DEFAULT_SHUTDOWN_PROGRESS_FILE,
        help="If this file exists, readiness checks will fail",
    )

    args = parser.parse_args()

    if not check_ready(
        stats_socket=args.stats_socket,
        queue_threshold=args.queue_threshold,
        shutdown_file=args.shutdown_progress_file,
    ):
        exit(-1)
