---
title: Inbound — Receiving
description: ASN, Receiving, Putaway — how goods enter the warehouse.
---

The inbound flow moves goods from a client's origin into assigned bins. It
spans three operational doctypes plus an auto-created Stock Entry.

## Step 1 — ASN (Advance Shipment Notice)

A client creates an **ASN** to announce an incoming shipment. Each ASN has
one or more **ASN Lines**, one per SKU + quantity + expected batch.

Fields that matter on the header:

- `client` — which 3PL customer this belongs to.
- `expected_arrival` — used for dock scheduling.
- `warehouse_job` — auto-created on submit if blank.

On submit, the ASN is available for the receiving team.

## Step 2 — Receiving

From an ASN, the operator runs **Create Receiving** (backed by
`ASN.make_receiving()`). This maps the ASN into a new **Receiving** doc
where the operator enters the **actual** quantities, batches and QC status.

Typical differences the operator records:

| ASN said | Received reality |
|---|---|
| 100 cartons SKU-A | 98 cartons — 2 damaged |
| Batch B-2026-04 | Batch B-2026-04 + trace a split shipment |
| QC pending | QC passed / held / rejected |

Rejected or held lines stay visible but do not advance to putaway.

## Step 3 — Putaway Task

Submitting Receiving generates **Putaway Tasks** — one per accepted line.
The task suggests a destination bin using the
[Putaway Engine](/guide/engines/), which looks at:

1. The item's `storage_temp_zone`.
2. The client's `default_temp_zone`.
3. Bin `capacity`, `velocity_class`, and existing mix rules.

The operator may override the suggestion. Running **Complete Putaway**
(`Putaway Task.complete_putaway()`) performs three things:

1. Moves stock from the receiving staging bin to the target bin.
2. Creates a zero-value **Stock Entry** in ERPNext.
3. Logs a **Billing Transaction** for the inbound activity.

## What's logged automatically

- **Stock Entry** on the ERPNext Stock module — zero valuation, client and
  warehouse_job set on custom fields.
- **Job Stock Movement** child row on the Warehouse Job Record.
- **Billing Transaction** — the rate is resolved from the client's active
  Rate Card (e.g. "Inbound handling per pallet").

## Troubleshooting

- **Putaway suggestion is empty** — the Putaway Engine couldn't find a bin
  matching the temperature zone and capacity constraints. Widen the
  [Inventory Policy](/reference/policy-engine/) for the client, or free up
  a suitable bin.
- **Stock Entry didn't create** — check that the item has a default Item
  Group and that the Receiving line has an accepted `qc_status`.
- **No Billing Transaction** — confirm the client has an `active_rate_card`
  and that the Rate Card has a line for the inbound activity type.
