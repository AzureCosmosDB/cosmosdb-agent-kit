#!/usr/bin/env bash
set -euo pipefail
cd /app

# The azure-cosmos Java v4 SDK always uses TLS for its Gateway connection, so
# this instance talks to the emulator over https (see the task Dockerfile).
# The emulator signs its localhost cert with a self-signed root CA; trust that
# CA so the SDK's TLS handshake succeeds. No-op for real accounts.
if [[ "${COSMOS_ENDPOINT:-}" == https://localhost* || "${COSMOS_ENDPOINT:-}" == https://127.0.0.1* ]]; then
  TRUSTSTORE="${JAVA_HOME}/lib/security/cacerts"
  imported=0
  # Preferred: the emulator's root CA on the shared filesystem.
  if [[ -r /scripts/certs/rootCA.crt ]]; then
    keytool -importcert -noprompt -trustcacerts -alias cosmos-emulator-root \
      -file /scripts/certs/rootCA.crt -keystore "$TRUSTSTORE" -storepass changeit \
      >/dev/null 2>&1 && imported=1 || true
  fi
  # Fallback: whatever the gateway serves at /_explorer/emulator.pem.
  if [[ "$imported" -eq 0 ]]; then
    for _ in $(seq 1 30); do
      if curl -sk "${COSMOS_ENDPOINT}/_explorer/emulator.pem" -o /tmp/emu.pem 2>/dev/null \
        && [[ -s /tmp/emu.pem ]]; then
        keytool -importcert -noprompt -trustcacerts -alias cosmos-emulator \
          -file /tmp/emu.pem -keystore "$TRUSTSTORE" -storepass changeit \
          >/dev/null 2>&1 || true
        break
      fi
      sleep 1
    done
  fi
fi

exec java -jar target/mosaic-users.jar
