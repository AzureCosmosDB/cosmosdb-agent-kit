"use strict";

/**
 * Payload validation and sanitization for cosmosdb-best-practices telemetry.
 *
 * This module is the privacy guardrail. It accepts an arbitrary parsed JSON
 * object and returns a strictly whitelisted, validated event. Anything not on
 * the allowlist — and any value that fails validation — is dropped. No code,
 * prompts, file paths, or user identity can pass through.
 */

const crypto = require("crypto");

const SCHEMA_VERSION = "1.0";
const SKILL_NAME = "cosmosdb-best-practices";

const ALLOWED_EVENTS = new Set(["skill_activated", "skill_installed", "rules_applied"]);
const ALLOWED_LANGUAGES = new Set([
  "dotnet",
  "java",
  "python",
  "go",
  "javascript",
  "typescript",
  "unknown",
]);
const ALLOWED_AGENT_HOSTS = new Set(["copilot", "claude", "cursor", "other"]);

const SEMVER_RE = /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/;
const RULE_ID_RE = /^[a-z][a-z0-9-]{1,60}$/;
const GUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const MAX_RULES = 50;

function coerceEnum(value, allowed, fallback) {
  return typeof value === "string" && allowed.has(value) ? value : fallback;
}

function sanitizeRules(rules) {
  if (!Array.isArray(rules)) {
    return [];
  }
  const seen = new Set();
  for (const raw of rules) {
    if (typeof raw !== "string") {
      continue;
    }
    const rule = raw.trim().toLowerCase();
    if (RULE_ID_RE.test(rule)) {
      seen.add(rule);
    }
    if (seen.size >= MAX_RULES) {
      break;
    }
  }
  return Array.from(seen);
}

/**
 * @param {object} input - Untrusted, parsed JSON payload.
 * @returns {{ ok: true, event: object } | { ok: false, error: string }}
 */
function sanitize(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    return { ok: false, error: "payload must be a JSON object" };
  }

  const event = coerceEnum(input.event, ALLOWED_EVENTS, null);
  if (!event) {
    return {
      ok: false,
      error: `event must be one of: ${Array.from(ALLOWED_EVENTS).join(", ")}`,
    };
  }

  const language = coerceEnum(input.language, ALLOWED_LANGUAGES, "unknown");
  const agentHost = coerceEnum(input.agentHost, ALLOWED_AGENT_HOSTS, "other");
  const rules = sanitizeRules(input.rules);

  const skillVersion =
    typeof input.skillVersion === "string" && SEMVER_RE.test(input.skillVersion)
      ? input.skillVersion
      : undefined;

  const sessionId =
    typeof input.sessionId === "string" && GUID_RE.test(input.sessionId)
      ? input.sessionId.toLowerCase()
      : crypto.randomUUID();

  return {
    ok: true,
    event: {
      schemaVersion: SCHEMA_VERSION,
      event,
      skillName: SKILL_NAME,
      skillVersion,
      language,
      agentHost,
      rules,
      ruleCount: rules.length,
      sessionId,
    },
  };
}

/**
 * Maps a sanitized event to Application Insights trackEvent shape.
 * @param {object} evt - Output of sanitize().event
 */
function toTrackEvent(evt) {
  const properties = {
    schemaVersion: evt.schemaVersion,
    event: evt.event,
    skillName: evt.skillName,
    language: evt.language,
    agentHost: evt.agentHost,
    sessionId: evt.sessionId,
  };
  if (evt.skillVersion) {
    properties.skillVersion = evt.skillVersion;
  }
  if (evt.rules.length > 0) {
    properties.rules = evt.rules.join(",");
  }

  return {
    name: "SkillUsage",
    properties,
    measurements: { ruleCount: evt.ruleCount },
  };
}

module.exports = {
  SCHEMA_VERSION,
  SKILL_NAME,
  ALLOWED_EVENTS,
  ALLOWED_LANGUAGES,
  ALLOWED_AGENT_HOSTS,
  sanitize,
  toTrackEvent,
};
