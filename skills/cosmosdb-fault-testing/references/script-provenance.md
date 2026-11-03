# PPAF script provenance

Use the bundled `scripts/EnableDisableChaosFault.ps1` relative to the installed
skill root. It is an unmodified snapshot, not an automatically updated download.

| Field | Value |
|-------|-------|
| Upstream | [AzureCosmosDB/ppaf-samples](https://github.com/AzureCosmosDB/ppaf-samples) |
| Revision | `84105f271ec042a016f3e69b8911edbfd80fea14` |
| Source path | `ppaf-fault-script/EnableDisableChaosFault.ps1` |
| SHA-256 (exact bytes) | `cdc4727bb1ea288f1f65319261cc3780eec29b7d3e7b5b7b251404e2c5f3c25f` |
| License | MIT; see [bundled license](../LICENSE) |

The contributor confirmed permission to redistribute this snapshot under MIT
on 2026-11-02. The pinned upstream tree has no license file; this statement
records the permission for this package, not a license claim about other
upstream content.

This hash identifies the reviewed snapshot. It is not a guarantee of
compatibility with every service deployment. Offline mocked execution covers
status, enable, and disable command paths; it is not end-to-end live validation.
Read [PPAF limitations and supervision](ppaf.md) before use, particularly
fixed waits, subscription changes, field casing, and independent state observation.

## Verify before use

Resolve `<installed-skill-root>` from the skill's actual installation location,
not the current working directory. Do not run these commands with placeholders.

```powershell
$skillRoot = '<installed-skill-root>'
$scriptPath = Join-Path $skillRoot 'scripts/EnableDisableChaosFault.ps1'
$expectedHash = 'cdc4727bb1ea288f1f65319261cc3780eec29b7d3e7b5b7b251404e2c5f3c25f'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $scriptPath).Hash -ine $expectedHash) {
    throw 'Bundled PPAF script hash mismatch; stop before execution.'
}
Get-Content -Raw -LiteralPath $scriptPath
```

## Optional download or update

- [Download the identical pinned source](https://raw.githubusercontent.com/AzureCosmosDB/ppaf-samples/84105f271ec042a016f3e69b8911edbfd80fea14/ppaf-fault-script/EnableDisableChaosFault.ps1):
  save to a new scratch file and verify the hash above before selecting it.
- [Inspect upstream changes](https://github.com/AzureCosmosDB/ppaf-samples/commits/main/ppaf-fault-script/EnableDisableChaosFault.ps1):
  select an immutable commit, download into a separate file, compare with the
  bundle, inspect behavior/permissions/dependencies and licensing, and run offline
  compatibility checks. Record the candidate revision/hash and obtain explicit
  approval before execution. Retain the approved matching recovery version.

Never pipe downloaded content into execution or overwrite the bundle during
a drill. A newer hash is not covered by the snapshot's validation. If the bundle
is missing or modified, stop and repair from the pinned source with approval;
do not silently fall back to `main`. Maintainer updates must change the snapshot,
recorded revision/hash, and offline expectations together.
