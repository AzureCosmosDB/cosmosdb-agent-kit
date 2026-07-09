#!/usr/bin/env node
"use strict";

/**
 * report-usage.js — First-party, PII-free usage telemetry for the
 * cosmosdb-best-practices skill.
 *
 * This CLI is meant to be shelled out to by the skill (or an eval harness).
 * It is best-effort by design: it ALWAYS exits 0 and never throws to the
 * caller, so it can never break an agent's task.
 *
 * Usage:
 *   node report-usage.js --data '{"event":"skill_activated","language":"dotnet"}'
 *   echo '{"event":"rules_applied","rules":["sdk-singleton-client"]}' | node report-usage.js
 *   node report-usage.js --dry-run --data '{"event":"skill_activated"}'
 *
 * Flags:
 *   --data <json>   Inline JSON payload. If omitted, payload is read from stdin.
 *   --dry-run       Validate + print the sanitized event; do not send.
 *   --help          Print usage.
 *
 * Config (environment):
 *   COSMOSDB_SKILLS_APPINSIGHTS_CONNECTION_STRING   App Insights connection string.
 *                                                   If unset, telemetry no-ops.
 *   COSMOSDB_SKILLS_TELEMETRY_DISABLED=1            Hard opt-out.
 */

const { sanitize, toTrackEvent } = require("./sanitize");
const client = require("./client");

function parseArgs(argv) {
  const args = { dryRun: false, help: false, data: undefined };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--dry-run") {
      args.dryRun = true;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--data") {
      args.data = argv[++i];
    } else if (arg.startsWith("--data=")) {
      args.data = arg.slice("--data=".length);
    }
  }
  return args;
}

function readStdin() {
  return new Promise((resolve) => {
    if (process.stdin.isTTY) {
      resolve("");
      return;
    }
    let buffer = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      buffer += chunk;
    });
    process.stdin.on("end", () => resolve(buffer));
    process.stdin.on("error", () => resolve(""));
  });
}

const HELP = `report-usage.js — PII-free telemetry for cosmosdb-best-practices

Usage:
  node report-usage.js --data '<json>'
  echo '<json>' | node report-usage.js
  node report-usage.js --dry-run --data '<json>'

Payload fields (all optional except "event"):
  event       skill_activated | rules_applied        (required)
  language    dotnet|java|python|go|javascript|typescript|unknown
  agentHost   copilot|claude|cursor|other
  rules       ["sdk-singleton-client", ...]           (rule IDs only)
  skillVersion  e.g. "1.1.0"
  sessionId   anonymous GUID (generated if omitted)

Any other field is ignored. Malformed values are dropped.

Env:
  ${client.CONNECTION_STRING_ENV}   target App Insights (unset => no-op)
  ${client.DISABLE_ENV}=1                              hard opt-out
`;

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    process.stdout.write(HELP);
    return 0;
  }

  const raw = args.data !== undefined ? args.data : await readStdin();
  if (!raw || !raw.trim()) {
    process.stderr.write("[telemetry] no payload provided; skipping\n");
    return 0;
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (_err) {
    process.stderr.write("[telemetry] invalid JSON payload; skipping\n");
    return 0;
  }

  const result = sanitize(parsed);
  if (!result.ok) {
    process.stderr.write(`[telemetry] ${result.error}; skipping\n`);
    return 0;
  }

  const trackEvent = toTrackEvent(result.event);

  if (args.dryRun) {
    process.stdout.write(JSON.stringify(trackEvent, null, 2) + "\n");
    return 0;
  }

  const outcome = await client.send(trackEvent);
  if (outcome.sent) {
    process.stderr.write("[telemetry] event sent\n");
  } else {
    process.stderr.write(`[telemetry] not sent (${outcome.reason})\n`);
  }
  return 0;
}

main()
  .then((code) => process.exit(code || 0))
  .catch((err) => {
    // Absolute last-resort guard: never surface a non-zero exit to the agent.
    process.stderr.write(`[telemetry] unexpected error: ${err && err.message}\n`);
    process.exit(0);
  });
