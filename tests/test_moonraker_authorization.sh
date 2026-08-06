#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../scripts/moonraker_authorization.sh"

work_dir="$(mktemp -d)"
trap 'rm -rf "${work_dir}"' EXIT

config_file="${work_dir}/moonraker.conf"
cat > "${config_file}" <<'EOF'
[server]
host: 0.0.0.0

[authorization]
trusted_clients:
  192.168.1.0/24
  # Keep this comment
  10.0.0.5

[file_manager]
EOF

if moonraker_local_client_is_trusted "${config_file}"; then
    echo "Expected missing loopback authorization to be reported" >&2
    exit 1
fi

add_moonraker_local_client "${config_file}"

moonraker_local_client_is_trusted "${config_file}"
grep -Fxq '  127.0.0.1' "${config_file}"
grep -Fxq '  # Keep this comment' "${config_file}"
grep -Fxq '[file_manager]' "${config_file}"

moonraker_url_uses_default_localhost 'http://localhost:7125'
moonraker_url_uses_default_localhost 'http://127.0.0.1:7125/'
if moonraker_url_uses_default_localhost 'http://192.168.1.10:7125'; then
    echo "Expected remote Moonraker URL to be skipped" >&2
    exit 1
fi

echo "Moonraker authorization helper tests passed"
