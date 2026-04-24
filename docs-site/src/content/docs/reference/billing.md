---
title: Billing Reference
description: Activity types, Rate Card fields, and how Billing Transactions roll into Sales Invoices.
---

Warehouse 3PL's billing model is: **every priced warehouse activity emits
a Billing Transaction, keyed by an `activity_type` constant**. Rate Card
Lines price those constants per client. At invoicing time, open Billing
Transactions are grouped into an ERPNext Sales Invoice.

## Activity types

The constants the billing engine knows about, grouped by flow:

| Flow | `activity_type` | Unit |
|---|---|---|
| Inbound | `inbound_per_pallet` | pallet |
| Inbound | `inbound_per_carton` | carton |
| Inbound | `inbound_per_line` | line |
| Storage | `storage_per_pallet_day` | pallet·day |
| Storage | `storage_per_carton_day` | carton·day |
| Storage | `storage_per_cbm_day` | cbm·day |
| Outbound | `pick_per_line` | line |
| Outbound | `pick_per_unit` | unit |
| Outbound | `pack_per_carton` | carton |
| Outbound | `pack_per_order` | order |
| Outbound | `outbound_handoff` | shipment |
| Surcharges | `hazmat_surcharge` | shipment |
| Surcharges | `peak_season_surcharge` | shipment |
| Surcharges | `manual_adjustment` | — (typed in by hand) |

## Rate Card Line fields

| Field | Purpose |
|---|---|
| `activity_type` | Must match one of the constants above. |
| `uom` | Unit this rate is priced by. |
| `rate` | Per-unit price. |
| `min_charge` | Applied if `qty × rate < min_charge`. |
| `rounding_rule` | `round_half_up`, `ceil`, `floor`, `none`. |
| `effective_from` / `effective_to` | Optional validity window. |
| `notes` | Free-text — not used by the engine. |

Multiple lines for the same `activity_type` are allowed, disambiguated by
the effective dates. The engine picks the line valid on the activity
date.

## Billing Transaction fields

| Field | Purpose |
|---|---|
| `client` | Customer. |
| `warehouse_job` | Link to Warehouse Job Record. |
| `activity_type` | One of the constants above. |
| `quantity` | The billable quantity. |
| `rate` | Resolved rate at activity time. |
| `amount` | `quantity × rate` with rounding applied. |
| `source_doctype` / `source_name` | What created this BT (Pick Task, Pack Task, …). |
| `activity_date` | Used for rate-card effective-date resolution. |
| `status` | `open`, `needs_review`, `invoiced`, `cancelled`. |
| `sales_invoice` | Populated when the BT is rolled into an SI. |

## How invoicing works

1. A finance user opens the **Billing Transactions** list, filters by
   `client` and `status = open`, and selects rows.
2. Running the **Create Sales Invoice** action groups the selection by
   client and writes one SI per client.
3. On SI submit, each BT's `status` moves to `invoiced` and its
   `sales_invoice` link is set.
4. The SI itself carries the `warehouse_job` custom field where
   applicable, so ops can trace back from an invoice line to the job.

## Programmatic usage

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

If a matching Rate Card Line isn't found, the BT is created with
`amount = 0` and `status = needs_review` — the row is never silently
dropped, so unbilled activity is always visible.

## Troubleshooting

- **`needs_review` BTs piling up** — the client's Rate Card is missing a
  line for an activity type you're generating. Add the line and
  re-compute amounts with the `billing.recompute` console helper.
- **Wrong rate applied** — check the effective dates on the Rate Card
  Line; the engine uses `activity_date` on the BT, not today.
- **P&L on Warehouse Job Record looks off** — drafts count. Check
  `Job Voucher` child table for an unsubmitted Purchase Invoice.
