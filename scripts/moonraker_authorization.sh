#!/usr/bin/env bash

# Helpers for validating the local Moonraker HTTP client configured by the
# installer. Moonraker treats trusted clients as fully authorized API clients.

moonraker_local_client_is_trusted() {
    local moonraker_conf="$1"

    awk '
        BEGIN { in_authorization=0; in_trusted_clients=0; found=0 }
        /^\[authorization\][[:space:]]*$/ {
            in_authorization=1
            next
        }
        in_authorization && /^\[/ { exit }
        in_authorization && /^[[:space:]]*trusted_clients:[[:space:]]*$/ {
            in_trusted_clients=1
            next
        }
        in_authorization && in_trusted_clients && /^[[:space:]]+/ {
            value=$0
            sub(/^[[:space:]]+/, "", value)
            if (value == "127.0.0.1") {
                found=1
                exit
            }
            next
        }
        in_trusted_clients { in_trusted_clients=0 }
        END { exit(found ? 0 : 1) }
    ' "$moonraker_conf"
}

add_moonraker_local_client() {
    local moonraker_conf="$1"
    local temporary_file="${moonraker_conf}.auto_power_off.tmp"

    awk '
        BEGIN { in_authorization=0; found_authorization=0; added=0 }
        /^\[authorization\][[:space:]]*$/ {
            in_authorization=1
            found_authorization=1
            print
            next
        }
        in_authorization && /^\[/ {
            if (!added) {
                print "trusted_clients:"
                print "  127.0.0.1"
                added=1
            }
            in_authorization=0
        }
        in_authorization && /^[[:space:]]*trusted_clients:[[:space:]]*$/ {
            print
            print "  127.0.0.1"
            added=1
            next
        }
        { print }
        END {
            if (!found_authorization) {
                print ""
                print "[authorization]"
                print "trusted_clients:"
                print "  127.0.0.1"
            } else if (in_authorization && !added) {
                print "trusted_clients:"
                print "  127.0.0.1"
            }
        }
    ' "$moonraker_conf" > "$temporary_file" && mv "$temporary_file" "$moonraker_conf"
}

moonraker_url_uses_default_localhost() {
    local moonraker_url="$1"
    [[ "$moonraker_url" =~ ^http://(localhost|127\.0\.0\.1):7125/?$ ]]
}
