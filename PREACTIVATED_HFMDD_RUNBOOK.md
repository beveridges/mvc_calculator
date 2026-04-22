# Preactivated Institutional Runbook (@hfmdd.de)

This runbook defines the operator workflow for producing a preactivated institutional build that ships with a bundled entitlement.

## Scope

- Target audience: `@hfmdd.de` institutional deployment.
- Activation mode: bundled preactivated entitlement (`license_key_v1`).
- Runtime enforcement remains enabled; no bypass mode is used.

## Prerequisites

- Repository checked out and build environment ready.
- A valid wildcard institutional license key for `@hfmdd.de`.
- Python environment with project dependencies.

## 1) Issue wildcard institutional key

Generate a wildcard license key (DE country example):

```bash
python generate_license.py institutional@hfmdd.de DE 0 --wildcard-hfmdd
```

This writes `license.key` in the working directory.

## 2) Build entitlement artifact

Convert `license.key` to standard preactivated entitlement payload:

```bash
python scripts/build_preactivated_entitlement.py ^
  --license-file license.key ^
  --output preactivated/entitlement.json ^
  --issued-for hfmdd.de ^
  --bundle-id HFMDD-YYYYMM
```

Artifact format:

- `format: license_key_v1`
- `license_key: <signed key>`
- `source: preactivated_bundle`
- `issued_for: hfmdd.de`
- optional `bundle_id`

## 3) Build preactivated package

Use the entitlement artifact as build input.

Windows:

```bash
python BUILD_ALL_WINDOWS.py --preactivated-entitlement preactivated/entitlement.json
```

Linux:

```bash
python BUILD_ALL_LINUX.py --preactivated-entitlement preactivated/entitlement.json
```

Result:

- Build scripts bundle artifact at `preactivated/entitlement.json` inside packaged files.
- On first app run, the app auto-installs this entitlement into user data path.

## 4) Validation checklist

- Fresh machine launch should unlock features immediately.
- If user data entitlement is deleted, app should return to activation-required state.
- If bundled entitlement is invalid/tampered, app should remain locked.

## 5) Rotation / re-issue procedure

When rotating institutional entitlement:

1. Issue a new wildcard institutional key.
2. Regenerate `preactivated/entitlement.json` with a new `bundle_id`.
3. Rebuild package with `--preactivated-entitlement`.
4. Communicate that reinstalling updates entitlement on target machines.

## 6) Security notes

- Do not commit production entitlement artifacts to git.
- Keep generated `license.key` and entitlement files in secure operator storage.
- Keep `LICENSE_SECRET` protected and changed per production policy.

## 7) Runtime behaviour (preactivated bundle installs)

- **Country check:** For entitlements whose JSON `source` is `preactivated_bundle`, the app **does not** block on detected country vs country embedded in the licence key. Wildcard `@hfmdd.de` rules and signature validation still apply. Other entitlement sources (migrated `license.key`, activation, etc.) keep the normal country match.
- **Launch telemetry email:** On each successful startup with a `preactivated_bundle` entitlement, the app **silently** queues a detailed report to **telemetry@moviolabs.com** (background thread; failures are logged only, no user dialog). Ensure the institution accepts transmission of host identifiers (HWID, hostname, OS user, country hints, etc.) under your agreement.
- **Disable launch reports:** Set environment variable `PREACTIVATED_LAUNCH_REPORT` to `0`, `false`, `no`, or `off` before starting the app if a deployment must not send these messages.
