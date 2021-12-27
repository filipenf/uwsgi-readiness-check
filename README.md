# uwsgi-readiness-check

Readiness check for uwsgi using its stats socket

Use this check to mark a pod running `uwsgi` as `NotReady` whenever the uwsgi queue crosses a threshold.
This will allow uwsgi to finish processing requests in its queue before Kubernetes sends more traffic to it 

# Local Development / Testing

Because the readiness check needs to run as part of a pod, in order to have functional test we deploy
a small python+uwsgi application that sleeps for a few seconds + a second python "client" script that
makes requests. Since the application sleeps upon a request and new requests are constantly being sent,
uwsgi will eventually queue and we'll readiness checks should fail.

[Kind installation](https://kind.sigs.k8s.io/docs/user/quick-start/)
[Skaffold installation](https://skaffold.dev/docs/install/#standalone-binary)
[Kubectl installation](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)

## Running locally

With `kind`, `kubectl` and `skaffold` installed, simply run:

```
skaffold dev
```

Skaffold builds a docker image, loads into the kind "cluster" and creates the Pods, watches for changes in
the filesystem and automatically re-deploys when needed.

# Examples:

The example below will prevent traffic from hitting the Pod once the queue reaches 70% its max capacity:

```
          readinessProbe:
            exec:
              command:
                - uwsgi-is-ready
                - --stats-socket
                - /tmp/uwsgi-stats
                - --queue-threshold
                - 0.7
            failureThreshold: 2
            initialDelaySeconds: 5
            periodSeconds: 5
            successThreshold: 1
            timeoutSeconds: 1
```

You can find a complete example in `k8s/deployment.yaml`

# Installation

In the container image used by your Pod, run:

```
pip install uwsgi-readiness-check
```