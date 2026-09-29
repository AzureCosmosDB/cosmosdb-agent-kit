---
title: Scope, preview, and confirm Cosmos DB Shell writes and deletions
impact: HIGH
impactDescription: prevents unintended data loss, unexpected cost changes, and duplicate writes
tags: tooling, cosmosdb-shell, mcp, writes, destructive-operations, safety
---

## Scope, Preview, and Confirm Cosmos DB Shell Writes and Deletions

A request to inspect or diagnose data is not permission to change it. Run writes through Cosmos DB Shell only when the user asks for them. Before a write, verify the account (see `tooling-cosmosdb-shell-target`), database, container, and the affected item's `id` and partition key, and read the current state when relevant.

**Incorrect (deleting by an assumed ID, relying on navigation, and trying to skip confirmation):**

```text
cd Orders
rm order-123                          # pattern matches the partition key by default, not id
rmdb OldDb true                       # force skips only the interactive prompt, not MCP confirmation
```

**Correct (verify the item and partition, preview, then confirm):**

```text
info --database=MyDb --container=Orders  # confirm the partition key path is /customerId
query "SELECT c.id, c.customerId FROM c WHERE c.id = 'order-123'" --database=MyDb --container=Orders --max=2
# Stop if results are incomplete, multiple items share the ID, or the intended partition key is unknown.
rm order-123 --key=id --database=MyDb --container=Orders --dry-run
# Proceed only if the query identifies the intended partition key and the dry-run count is exactly 1.
rm order-123 --key=id --database=MyDb --container=Orders
# Use the partition key value verified above; customer-42 is only an example.
query "SELECT c.id FROM c WHERE c.id = 'order-123' AND c.customerId = 'customer-42'" --database=MyDb --container=Orders --max=1
```

- **Match the right item.** `rm` and `delete item` patterns match the partition key by default; `--key=id` matches the ID across *all* partitions, where the same ID may occur more than once. Wildcards such as `test-*` can match many items. Verify the intended ID and partition key before deleting. The example's `customer-42` must be the verified partition key value, not an assumed one.
- **Account for a full scan.** `rm` reads every item with `SELECT * FROM c` to match the pattern, even with `--key=id` and `--dry-run`. Both preview and deletion can consume substantial RUs on large containers. Explain that cost before proceeding; if a scan is unacceptable, stop and discuss alternatives rather than silently switching tools or bypassing confirmation.
- **Check the preview, not just its completion.** `--dry-run` returns a match count, not the item identities. For a single-item request, proceed only if that count is exactly one and a bounded query confirms the matching item's partition key. If the count is zero, greater than one, or otherwise uncertain, stop and clarify. A preview is not an atomic guarantee that the data cannot change before deletion. `rmcon`, `rmdb`, and `delete` also support `--dry-run`.
- **Explain consequences first.** Before running an import, batch, patch, replace, indexing, throughput, or TTL change, describe its scope and effect. `create ... -force` upserts and can overwrite items. `ttl set` and `ttl on` can cause items to expire. Throughput changes affect cost. Clarify ambiguous targets or effects before acting.
- **Honor the confirmation gate.** Invoke `delete`, `rm`, `rmcon`, and `rmdb` only for an explicit user request, and remind the user to back up important data. The MCP server shows the command, endpoint, and navigation location, then asks the user to approve it. Force arguments do not bypass this prompt. Never use a terminal, another tool, or a different command to work around it.
- **Stop when confirmation fails.** A declined prompt is not permission to try another route. If the client cannot display the prompt, the server refuses the command; give the user the verified command to run manually. If the connection or navigation changed while confirmation was pending, the server refuses the command. Re-verify the target before trying again.
- **Verify the outcome.** After a write, confirm the result with a narrow, bounded read. If a call times out or its outcome is unclear, inspect the current state before retrying so that non-idempotent writes are not duplicated. Through MCP, transactional batches must use the one-shot `batch run`; stateful batch subcommands are available only in the interactive shell.

Reference: [MCP destructive command confirmation](https://github.com/Azure/CosmosDBShell/blob/main/docs/mcp.md#destructive-command-confirmation)
