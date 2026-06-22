#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/debian"
DIST_DIR="${DEVCAPSULE_DIST_DIR:-${ROOT_DIR}/dist}"
PACKAGE_NAME="devcapsule"
MAINTAINER="DevCapsule contributors <maintainers@devcapsule.local>"
DESCRIPTION="Local-first AI context collection tool for developers"

cd "${ROOT_DIR}"

VERSION="$(
  python - <<'PY'
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["version"])
PY
)"

ARCH="$(dpkg --print-architecture)"
PKG_ROOT="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}"
PEX_PATH="${BUILD_DIR}/${PACKAGE_NAME}.pex"
CONTROL_DIR="${PKG_ROOT}/DEBIAN"

rm -rf "${BUILD_DIR}"
mkdir -p "${DIST_DIR}" "${CONTROL_DIR}" "${PKG_ROOT}/opt/devcapsule" \
  "${PKG_ROOT}/usr/bin" "${PKG_ROOT}/usr/share/doc/devcapsule"

python -m pip install --root-user-action=ignore --upgrade pip build pex
python -m build --wheel --outdir "${BUILD_DIR}/wheel"

WHEEL_FILE="$(find "${BUILD_DIR}/wheel" -name '*.whl' -print -quit)"
if [[ -z "${WHEEL_FILE}" ]]; then
  echo "No wheel was produced" >&2
  exit 1
fi

python -m pex "${WHEEL_FILE}" \
  --output-file "${PEX_PATH}" \
  --console-script devcapsule \
  --python-shebang '/usr/bin/env python3' \
  --disable-cache

install -m 0755 "${PEX_PATH}" "${PKG_ROOT}/opt/devcapsule/devcapsule.pex"
install -m 0644 README.md "${PKG_ROOT}/usr/share/doc/devcapsule/README.md"
install -m 0644 LICENSE "${PKG_ROOT}/usr/share/doc/devcapsule/LICENSE"

cat > "${PKG_ROOT}/usr/bin/devcapsule" <<'EOF'
#!/bin/sh
if ! command -v python3 >/dev/null 2>&1; then
  echo "devcapsule requires python3 >= 3.12" >&2
  exit 127
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
  echo "devcapsule requires python3 >= 3.12" >&2
  exit 1
fi

exec /opt/devcapsule/devcapsule.pex "$@"
EOF
chmod 0755 "${PKG_ROOT}/usr/bin/devcapsule"

INSTALLED_SIZE="$(du -ks "${PKG_ROOT}" | awk '{print $1}')"
cat > "${CONTROL_DIR}/control" <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: devel
Priority: optional
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Depends: python3, git
Recommends: xclip | wl-clipboard
Installed-Size: ${INSTALLED_SIZE}
Homepage: https://github.com/DevaanshPathak/DevCapsule
Description: ${DESCRIPTION}
 DevCapsule gathers local project context and renders it as AI-ready Markdown.
 It stores capture history locally in SQLite and does not upload project data.
EOF

dpkg-deb --build --root-owner-group "${PKG_ROOT}" "${DIST_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Built ${DIST_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
