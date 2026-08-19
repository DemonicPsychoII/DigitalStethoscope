#!/usr/bin/env bash
set -euo pipefail

: "${ZEPHYR_REVISION:?}"
: "${ZEPHYR_SDK_VERSION:?}"
: "${WEST_VERSION:?}"
root="$(git rev-parse --show-toplevel)"
ws="$root/.ci-workspace"
python3 -m venv "$ws/.venv"
py="$ws/.venv/bin/python"
west="$ws/.venv/bin/west"
"$py" -m pip install --disable-pip-version-check "west==$WEST_VERSION"
if [[ ! -d "$ws/zephyr/.git" ]]; then
  # west init passes --mr to git clone --branch, which does not accept a raw
  # commit SHA. Bootstrap from the named branch, then detach at the exact pin.
  "$west" init -m https://github.com/zephyrproject-rtos/zephyr --mr main "$ws"
fi
git -C "$ws/zephyr" fetch --depth=1 origin "$ZEPHYR_REVISION"
git -C "$ws/zephyr" checkout --detach "$ZEPHYR_REVISION"
(
  cd "$ws"
  "$west" update --narrow -o=--depth=1
  "$west" packages pip --install
  "$west" blobs fetch hal_espressif
  "$west" sdk install --version "$ZEPHYR_SDK_VERSION" -b "$ws" -t xtensa-espressif_esp32s3_zephyr-elf
  "$west" zephyr-export
)
