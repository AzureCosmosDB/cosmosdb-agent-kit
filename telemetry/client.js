"use strict";

/**
 * Thin wrapper around the OpenTelemetry-based `applicationinsights` SDK.
 *
 * Everything here is best-effort: if the SDK is not installed, no connection
 * string is configured, or the network call fails, we resolve without throwing
 * so the caller can always exit 0 and never block the agent.
 */

const CONNECTION_STRING_ENV = "COSMOSDB_SKILLS_APPINSIGHTS_CONNECTION_STRING";
const DISABLE_ENV = "COSMOSDB_SKILLS_TELEMETRY_DISABLED";

function isDisabled() {
  const flag = process.env[DISABLE_ENV];
  return flag === "1" || flag === "true";
}

function getConnectionString() {
  const value = process.env[CONNECTION_STRING_ENV];
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : undefined;
}

/**
 * @returns {{ enabled: boolean, reason?: string, connectionString?: string }}
 */
function getStatus() {
  if (isDisabled()) {
    return { enabled: false, reason: `${DISABLE_ENV} is set` };
  }
  const connectionString = getConnectionString();
  if (!connectionString) {
    return { enabled: false, reason: `${CONNECTION_STRING_ENV} is not set` };
  }
  return { enabled: true, connectionString };
}

/**
 * Sends a single trackEvent and flushes. Never throws.
 * @param {{ name: string, properties: object, measurements: object }} trackEvent
 * @returns {Promise<{ sent: boolean, reason?: string }>}
 */
async function send(trackEvent) {
  const status = getStatus();
  if (!status.enabled) {
    return { sent: false, reason: status.reason };
  }

  let appInsights;
  try {
    appInsights = require("applicationinsights");
  } catch (_err) {
    return {
      sent: false,
      reason: "applicationinsights SDK not installed (run npm install)",
    };
  }

  try {
    appInsights
      .setup(status.connectionString)
      .setAutoCollectConsole(false)
      .setAutoCollectExceptions(false)
      .setAutoCollectPerformance(false)
      .setAutoCollectRequests(false)
      .setAutoCollectDependencies(false)
      .setSendLiveMetrics(false);
    appInsights.start();

    const client = appInsights.defaultClient;
    client.trackEvent(trackEvent);

    const flushResult = client.flush();
    if (flushResult && typeof flushResult.then === "function") {
      await flushResult;
    }
    return { sent: true };
  } catch (err) {
    return { sent: false, reason: `send failed: ${err && err.message}` };
  }
}

module.exports = {
  CONNECTION_STRING_ENV,
  DISABLE_ENV,
  getStatus,
  send,
};
