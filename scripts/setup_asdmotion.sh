#!/usr/bin/env bash
set -euo pipefail

ASDMOTION_DIR="${1:-/opt/ASDMotion}"
PIP_SRC_DIR="${PIP_SRC_DIR:-/tmp/pip-src}"
VENV_DIR="${VENV_DIR:-/tmp/asdmotion-venv}"
REPO_URL="https://github.com/Dinstein-Lab/ASDMotion"
REPO_BRANCH="${REPO_BRANCH:-main}"

if [[ ! -d "$ASDMOTION_DIR/.git" ]]; then
  echo "Cloning ASDMotion into $ASDMOTION_DIR"
  if [[ "$ASDMOTION_DIR" == /opt/* ]] && [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "ASDMotion path under /opt usually needs sudo. Run this script with sudo or choose a writable path like /tmp/ASDMotion." >&2
    exit 1
  fi
  git clone "$REPO_URL" "$ASDMOTION_DIR"
fi

cd "$ASDMOTION_DIR"

tmp_requirements="/tmp/asdmotion.requirements.linux.fixed.txt"

sed -E 's/[[:space:]]*@ file:\/\/.*$//' requirements.txt \
  | sed '/^[[:space:]]*$/d' \
  | grep -Ev '^(mkl-fft|mkl-random|mkl-service==)' \
  > "$tmp_requirements"

python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
mkdir -p "$PIP_SRC_DIR"
python -m pip install --no-cache-dir --src "$PIP_SRC_DIR" -r "$tmp_requirements"

echo "ASDMotion install complete."
echo "Activate later with: source $VENV_DIR/bin/activate"
