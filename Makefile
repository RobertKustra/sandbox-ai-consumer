LOCAL_IMAGE ?= local:latest
TARGET_TAG ?= 1.0.6
TARGET_ENV ?= dev
OWNER ?= RobertKustra
OWNER_LC := $(shell printf '%s' "$(OWNER)" | tr '[:upper:]' '[:lower:]')
IMAGE ?= ghcr.io/$(OWNER_LC)/$(TARGET_ENV)/sandbox-ai-consumer:$(TARGET_TAG)

.PHONY: help check-git-clean build push print-target-tag print-image check-image-exists

help:
	@echo "Available targets:"
	@echo "  make build                - Build local Docker image after git clean check"
	@echo "  make push                 - Retag local image to IMAGE and push"
	@echo "  make check-git-clean      - Fail if working tree has uncommitted changes"
	@echo "  make print-target-tag      - Print TARGET_TAG"
	@echo "  make print-image           - Print IMAGE"
	@echo "  make check-image-exists    - Check if IMAGE already exists in registry"
	@echo "  OWNER=<github-owner> make push - Override GitHub owner"
	@echo "  LOCAL_IMAGE=<ref> make build - Override local image reference"
	@echo "  IMAGE=<ref> make push     - Override target image reference"
	@echo "  TARGET_ENV=<env> make push - Override target environment"
	@echo "  TARGET_TAG=<tag> make push - Override image tag"

print-target-tag:
	@echo $(TARGET_TAG)

print-image:
	@echo $(IMAGE)

check-git-clean:
	@if [ -n "$(shell git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean. Commit or stash all changes before build."; \
		git status --short; \
		exit 1; \
	fi

build: check-git-clean
	docker build -t $(LOCAL_IMAGE) .

check-image-exists:
	@if docker manifest inspect $(IMAGE) >/dev/null 2>&1; then \
		echo true; \
	else \
		echo false; \
	fi

push: build
	@if docker manifest inspect $(IMAGE) >/dev/null 2>&1; then \
		echo "Image already exists: $(IMAGE)"; \
		exit 0; \
	fi
	docker tag $(LOCAL_IMAGE) $(IMAGE)
	docker push $(IMAGE)