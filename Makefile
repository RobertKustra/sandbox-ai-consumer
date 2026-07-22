
LOCAL_IMAGE ?= sandbox-ai-consumer:0.1.0
IMAGE ?= ghcr.io/RobertKustra/dev/sandbox-ai-consumer:0.1.0

.PHONY: help check-git-clean build push

help:
	@echo "Available targets:"
	@echo "  make build    - Build local Docker image after git clean check"
	@echo "  make push     - Retag local image to IMAGE and push"
	@echo "  make check-git-clean - Fail if working tree has uncommitted changes"
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
