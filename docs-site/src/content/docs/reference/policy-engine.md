---
title: Policy Engine
description: Inventory Policy fields and how they are resolved per operation.
---

The **Inventory Policy** doctype is the knob most frequently tuned by
supervisors. One policy can cover a whole client or can be narrowed to a
single item group within one temperature zone.

## Resolution order

`policy_engine.resolve(client, item_group, zone)` walks from most-specific
to least-specific:

1. `client + item_group + zone`
2. `client + item_group`
3. `client`
4. Global default policy (the one with `is_default = 1`).

The first match wins. If nothing matches — including no global default — a
clear exception is raised rather than defaulting silently.

## Fields

### Scope

| Field | Purpose |
|---|---|
| `client` | Customer this policy applies to (blank = all clients). |
| `item_group` | Item Group scope (blank = all). |
| `temperature_zone` | Zone scope (blank = all). |
| `is_default` | One global fallback across the system. |
| `effective_from` / `effective_to` | Optional validity window. |

### Allocation

| Field | Purpose |
|---|---|
| `rotation_rule` | `FIFO`, `FEFO`, or `None`. |
| `allow_partial` | Whether a short-pick is acceptable (else the wave fails). |
| `batch_mix` | `Single` (one batch per pick) or `Mixed`. |
| `reserve_from_zone` | Restrict allocation to this zone's bins. |

### Putaway

| Field | Purpose |
|---|---|
| `putaway_strategy` | `forward_pick_first` / `bulk_first` / `nearest_empty`. |
| `respect_velocity_class` | Put A-class near pick face, C-class deep. |
| `prevent_mix_batches` | Forbid mixing batches in a single bin. |
| `prefer_same_zone` | Keep a client's stock together within a zone. |

### QC

| Field | Purpose |
|---|---|
| `qc_mandatory` | All receipts must pass QC before putaway. |
| `qc_sample_size` | Pieces per received batch to inspect. |
| `hold_on_fail` | Park the whole batch in `QC Hold` on any failure. |

## Examples

### Default policy (everyone)

```yaml
is_default: true
rotation_rule: FIFO
allow_partial: false
putaway_strategy: forward_pick_first
respect_velocity_class: true
qc_mandatory: false
```

### Frozen-only override for one client

```yaml
client: ACME
temperature_zone: Frozen
rotation_rule: FEFO       # expiry matters for frozen
prevent_mix_batches: true # no co-mingling
qc_mandatory: true
qc_sample_size: 5
```

### Hazmat item group

```yaml
item_group: Hazmat
rotation_rule: FIFO
reserve_from_zone: HazmatCage
putaway_strategy: bulk_first
prevent_mix_batches: true
```

## Debugging

If an allocation or putaway looks wrong, run the resolver from the console
to see which policy is winning:

```bash
bench --site your-site.localhost console
```

```python
from warehouse_3pl.utils import policy_engine
policy_engine.resolve(client="ACME", item_group="Widgets", zone="Ambient")
```

The returned doc's `name` is the one the engines will use.
