UID := $(shell id -u)
GID := $(shell id -g)

.PHONY: build
build:
	docker run --rm \
		--user $(UID):$(GID) \
		-v $(shell pwd):/build/ \
		-w /build/ \
		python:3.10.1-slim \
		python ./setup.py bdist --owner root --group root

.PHONY: test
test:
	echo To be implemented

