---
title: Architecture
description: How Warehouse 3PL is laid out — doctypes, engines, and extension points.
---

Warehouse 3PL is a standard Frappe app: a Python package with doctypes,
hooks, whitelisted methods, client scripts, and server-side utilities. It
does **not** fork ERPNext — it extends it via custom fields and runs
alongside it.

## Module layout

```
warehouse_3pl/
├── doctype/                    # 26 doctypes
│   ├── asn/                    # Advance Shipment Notice
│   ├── receiving/              # Goods receipt
│   ├── putaway_task/           # Bin assignment
│   ├── client_order/           # Outbound orders
│   ├── wave/                   # Batch processing
│   ├── pick_task/              # Warehouse picking
│   ├── pack_task/              # Packing operations
│   ├── warehouse_job_record/   # Central job hub
│   ├── warehouse_location/     # Bin-level storage
│   ├── inventory_policy/       # FIFO/FEFO rules
│   ├── rate_card/              # Client pricing
│   ├── billing_transaction/    # Activity billing
│   ├── client_item/            # Client SKU mapping
│   └── ... child tables & tracking docs
├── utils/
│   ├── allocation_engine.py    # FIFO/FEFO stock allocation
│   ├── policy_engine.py        # Inventory policy resolution
│   ├── putaway_engine.py       # Bin suggestion logic
│   └── billing.py              # Billing transaction creator
├── custom_fields/
│   └── setup.py                # ERPNext doctype extensions
└── workspace/
    └── warehouse_3pl.json      # Desk workspace layout
```

## Tech stack

- **Framework** — Frappe v15 (Python + MariaDB + Redis)
- **ERP layer** — ERPNext v15 (Stock, Accounts)
- **Python** — 3.10+
- **Frontend** — Frappe Desk (server-rendered JS forms)
- **Build** — `flit` for Python, `esbuild` for JS assets

## Relationship to ERPNext

Warehouse 3PL uses ERPNext as the stock + accounting backbone. Where it
needs extra information, it **adds custom fields** rather than shadowing
ERPNext tables. See [Custom Fields](/reference/custom-fields/) for the
full list.

| ERPNext doctype | Why we extend it |
|---|---|
| Customer | Flag and classify 3PL clients. |
| Warehouse | Encode bin location, zone, capacity. |
| Item | Track hazmat, lot, velocity, temperature class. |
| Batch | Supplier lot, country of origin, QC status. |
| Stock Entry | Back-link to client + warehouse_job. |
| Delivery Note | Carrier, tracking, wave, BOL. |
| Sales / Purchase Invoice | Back-link to warehouse_job for P&L. |

## Central document: Warehouse Job Record

Every operational doctype points to a **Warehouse Job Record**. That's
where dashboards, job-level P&L, and cross-referencing happens. See the
[Warehouse Job Record](/user/warehouse-job/) user page for the operator's
view.

## Utility engines

The `utils/` package is where the interesting logic lives. Keeping it in
plain Python modules (rather than doctype methods) makes it easy to unit
test.

| Module | Responsibility |
|---|---|
| `allocation_engine.py` | FIFO/FEFO stock allocation across bins. |
| `policy_engine.py` | Resolve Inventory Policy by client → item group → zone. |
| `putaway_engine.py` | Rank candidate bins for incoming stock. |
| `billing.py` | Create Billing Transactions from warehouse activities. |

See [Utility Engines](/guide/engines/) for their APIs.

## Hooks

Registered in `hooks.py`:

- **`after_install`** — runs `custom_fields.setup` to attach fields to
  ERPNext doctypes.
- **`doc_events`** — minimal; the heavy lifting is in whitelisted methods
  called by buttons on the forms.
- **`scheduler_events`** — currently quiet. A recurring billing sweep is
  on the roadmap (see [What's pending](#whats-built-vs-pending)).

## What's built vs pending

### Built and working
- All 26 doctypes with full CRUD.
- Inbound: ASN → Receiving → Putaway → Stock Entry.
- Outbound: Client Order → Wave → Pick → Pack → Delivery Note.
- Warehouse Job Record dashboard with stock summary and live P&L.
- Custom fields on ERPNext doctypes (installed by hook).
- Workspace with card sections and shortcuts.
- Utility engines and unit tests.

### Pending
- **Billing scheduler** — auto-sweep on a schedule.
- **Cold Chain module** — temperature monitoring and compliance.
- **Client Portal** — external-facing order/status visibility.
- **Enhanced Desk UI polish**.
- **Granular role-based permissions**.
- **REST API for external WMS/TMS integrations**.
