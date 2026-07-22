
LOCAL_IMAGE ?= local:latest
TARGET_TAG ?= 0.2.1
OWNER ?= RobertKustra
OWNER_LC := $(shell printf '%s' "$(OWNER)" | tr '[:upper:]' '[:lower:]')
IMAGE ?= ghcr.io/$(OWNER_LC)/dev/sandbox-ai-consumer:$(TARGET_TAG)

.PHONY: help check-git-clean build push

help:
	@echo "Available targets:"
	@echo "  make build    - Build local Docker image after git clean check"
	@echo "  make push     - Retag local image to IMAGE and push"
	@echo "  make check-git-clean - Fail if working tree has uncommitted changes"
	@echo "  OWNER=<github-owner> make push - Override GitHub owner (auto-lowercased for image path)"
	@echo "  LOCAL_IMAGE=<ref> make build - Override local image reference"
	@echo "  IMAGE=<ref> make push - Override target image reference"

check-git-clean:
	@if [ -n "$(shell git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean. Commit or stash all changes before build."; \
		git status --short; \
		exit 1; \
	fi

build: check-git-clean
	docker build -t $(LOCAL_IMAGE) .

push: build
	docker tag $(LOCAL_IMAGE) $(IMAGE)
	docker push $(IMAGE)
