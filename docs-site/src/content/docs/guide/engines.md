---
title: Utility Engines
description: Allocation, Policy, Putaway and Billing — the four engines that drive the flow.
---

All non-trivial logic in Warehouse 3PL is concentrated in four Python
modules under `warehouse_3pl/utils/`. They are plain functions — no
Frappe-specific boilerplate beyond reading and writing docs — which makes
them straightforward to unit test.

## `allocation_engine.py`

FIFO/FEFO stock allocation across bins for a given item + quantity.

```python
from warehouse_3pl.utils import allocation_engine

allocations = allocation_engine.allocate(
    client="ACME",
    item_code="ACME-WIDGET-01",
    qty=24,
    policy=policy_doc,  # Inventory Policy
)
# Returns a list of dicts:
# [{"warehouse": "A-04-02", "batch": "B-2026-04", "qty": 24, ...}]
```

Behaviour:

- **FIFO** — sort candidate batches by `receiving_date` ascending.
- **FEFO** — sort by `expiry_date` ascending; falls back to FIFO if no
  expiry is set.
- Respects `zone` restrictions from the policy.
- Short-picks are reported — the caller decides whether to split across
  replenishment or fail the wave.

## `policy_engine.py`

Resolves the **Inventory Policy** that applies to a given operation. The
lookup order is:

1. Client + Item Group + Zone (most specific).
2. Client + Item Group.
3. Client.
4. Global default policy.

```python
from warehouse_3pl.utils import policy_engine

policy = policy_engine.resolve(
    client="ACME",
    item_group="Widgets",
    zone="Ambient",
)
```

The returned Inventory Policy drives FIFO/FEFO, putaway candidates, and
QC behaviour. See [Policy Engine](/reference/policy-engine/) for the full
field list.

## `putaway_engine.py`

Ranks candidate bins for incoming stock. Inputs: item + quantity +
client. Outputs: a sorted list of `Warehouse Location` records.

Ranking inputs:

- Item `storage_temp_zone` must match the bin's `temperature_zone`.
- Bin has enough free capacity (volume / weight).
- Velocity class — "fast movers near the forward pick face".
- Avoid mixing batches when the policy forbids it.

```python
from warehouse_3pl.utils import putaway_engine

suggestions = putaway_engine.suggest(
    client="ACME",
    item_code="ACME-WIDGET-01",
    qty=98,
    staging_bin="RCV-STAGING-01",
)
```

The Putaway Task form calls this on load to pre-fill the suggested bin.

## `billing.py`

Writes Billing Transactions off the back of warehouse activities.

```python
from warehouse_3pl.utils import billing

billing.create_billing_transaction(
    client="ACME",
    warehouse_job="WJR-00231",
    activity_type="pack_per_carton",
    quantity=2,
    source_doctype="Pack Task",
    source_name="KP-0075",
)
```

Rate resolution:

1. Read the customer's `active_rate_card`.
2. Find a Rate Card Line with a matching `activity_type` and effective
   date range.
3. Apply `min_charge` and round per the Rate Card's `rounding_rule`.

If no rate is found, the BT is created with `amount = 0` and
`status = needs_review` so nothing is silently dropped.

## Testing

Each engine has a companion `test_*.py` next to it. Run everything with:

```bash
bench --site your-site.localhost run-tests --app warehouse_3pl
```

Run just one engine's tests:

```bash
bench --site your-site.localhost run-tests \
  --module "warehouse_3pl.warehouse_3pl.utils.test_allocation_engine"
```
