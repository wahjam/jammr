# Copyright (C) 2017-2024 Stefan Hajnoczi <stefanha@gmail.com>

HOSTS ?= docker,web,jam
TARGET ?= $(or $(file <.target),dev)
IMAGES = $(patsubst %/Dockerfile,%,$(wildcard */Dockerfile))
PUSH_IMAGES = $(patsubst %,push-%,$(IMAGES))
ANSIBLE = ANSIBLE_STDOUT_CALLBACK=debug bin/ansible-playbook -l $(HOSTS),localhost -e @secrets.yml -i inventories/$(TARGET)
WAHJAM2_DIR ?= $(realpath ../wahjam2)
APPNAME=jammr
ORGNAME="jammr ltd"
ORGDOMAIN=jammr.net
WAHJAM2_WINDOWS_BUILD_DIR ?= $(realpath ../wahjam2-windows-build)
WINDOWS_CODE_SIGNING_P12_FILE ?= $(realpath documents/2021/jammr_ltd.p12)
MAC_BUILD_HOST=mac-mini-m1
APPLE_ID=stefanha@gmail.com
TEAM_ID=SJ896596P8

# Do not honor make -j because this makefile doesn't specify dependencies
# between targets and 'deploy' could race with 'push-%' targets.
.NOTPARALLEL:

.PHONY: default all push-all help $(IMAGES) $(PUSH_IMAGES) host-setup client-windows client-mac deploy deploy-client use-dev use-staging use-prod setup-backup

default: webapp
all: $(IMAGES)
push-all: $(PUSH_IMAGES)

help:
	@echo 'Docker images:'
	@echo '  all               - build all images'
	@echo "  certbot           - build Let's Encrypt image"
	@echo '  exim4             - build mail server image'
	@echo '  jamd              - build jam session server image'
	@echo '  munin             - build munin image'
	@echo '  openssh-client    - build OpenSSH client image'
	@echo '  recorded-jams     - build recorded jams image'
	@echo '  webapp (default)  - build web application image'
	@echo
	@echo 'Clients:'
	@echo '  client-mac        - build macOS client'
	@echo '  client-windows    - build Windows client'
	@echo
	@echo 'Image transfer:'
	@echo '  push-all          - transfer all images to remote host'
	@echo '  push-IMAGE        - transfer image to remote host'
	@echo
	@echo 'Deployment:'
	@echo '  deploy            - launch containers on remote host'
	@echo '  deploy-client     - publish a new release of the client'
	@echo
	@echo 'Setup:'
	@echo '  host-setup        - install and configure remote host'
	@echo '  setup-backup      - configure backup between remote host'
	@echo '                      and backup host'
	@echo
	@echo 'Environments:'
	@echo '  TARGET=dev        - development (default)'
	@echo '  TARGET=prod       - production'
	@echo '  use-dev           - switch to development environment'
	@echo '  use-staging       - switch to staging environment'
	@echo '  use-prod          - switch to production environment'
	@echo
	@echo 'Ansible verbosity:'
	@echo '  V=1               - use ansible-playbook -vvv'
	@echo
	@echo 'Only run on specific hosts:'
	@echo '  HOSTS=a,b,c       - only run on hosts a, b, and c'
	@echo "$(IMAGES)"

use-dev:
	@echo 'dev' >.target
	@sudo sed -i 's/ #jammr.net/ jammr.net/' /etc/hosts
	@echo 'Using development environment'

use-staging:
	@echo 'staging' >.target
	@sudo sed -i 's/ jammr.net/ #jammr.net/' /etc/hosts
	@echo 'Using staging environment'

use-prod:
	@echo 'prod' >.target
	@sudo sed -i 's/ jammr.net/ #jammr.net/' /etc/hosts
	@echo 'Using production environment'

save_image = sudo $(ANSIBLE) --extra-vars "image_name=$1" playbooks/save-image.yml
push_image = $(ANSIBLE) --extra-vars "image_name=$1" playbooks/push-image.yml

$(IMAGES):
	cd "$@" && sudo docker build --network host --tag "$@:latest" --tag "$@:$$(git describe --always --dirty)" .

$(PUSH_IMAGES):
	$(call save_image,$(subst push-,,$@))
	$(call push_image,$(subst push-,,$@))
	rm -f "playbooks/$(subst push-,,$@).tar"

host-setup:
	$(ANSIBLE) playbooks/host-setup.yml

client-windows:
	cd "$(WAHJAM2_WINDOWS_BUILD_DIR)" && \
		CODE_SIGN_TOOL_USERNAME="$(shell python -c "import keyring; print(keyring.get_password('jammr-CodeSignTool', 'username'))")" \
		CODE_SIGN_TOOL_PASSWORD="$(shell python -c "import keyring; print(keyring.get_password('jammr-CodeSignTool', 'password'))")" \
		CODE_SIGN_TOOL_TOTP_SECRET="$(shell python -c "import keyring; print(keyring.get_password('jammr-CodeSignTool', 'totp_secret'))")" \
		podman run --rm -it --userns=keep-id -e APPNAME="$(APPNAME)" -e ORGNAME="$(ORGNAME)" -e ORGDOMAIN="$(ORGDOMAIN)" -e CODE_SIGN_TOOL_USERNAME -e CODE_SIGN_TOOL_PASSWORD -e CODE_SIGN_TOOL_TOTP_SECRET -v "$(WAHJAM2_DIR):/usr/src/wahjam2:z" wahjam2-windows-build

client-mac:
	cd "$(WAHJAM2_DIR)" && \
		ssh "$(MAC_BUILD_HOST)" 'cd wahjam2 && (git diff --quiet || (echo "Remote worktree is dirty, please stash or commit changes first." && false)) && git checkout main' && \
		git push "$(MAC_BUILD_HOST):wahjam2" +HEAD:jammr-build && \
		ssh "$(MAC_BUILD_HOST)" "cd wahjam2 && git checkout jammr-build && installer/darwin/make-installer.sh --appname \"$(APPNAME)\" --orgname \"$(ORGNAME)\" --orgdomain \"$(ORGDOMAIN)\" --apple-id \"$(APPLE_ID)\" --team-id \"$(TEAM_ID)\" --keychain-profile \"$(TEAM_ID)\" build"

deploy:
	$(ANSIBLE) playbooks/deploy.yml

deploy-client:
	$(ANSIBLE) playbooks/deploy-client.yml

setup-backup:
	$(ANSIBLE) playbooks/setup-backup.yml
