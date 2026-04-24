---
title: Getting Started
description: First-run setup for the Warehouse 3PL app on a Frappe bench.
---

This page gets you from a blank bench to a working 3PL site with one client
and a sample end-to-end job.

## Prerequisites

- Python **3.10+**
- Frappe **v15**
- ERPNext **v15**
- MariaDB **10.6+**
- Redis **6+**
- Node.js **18+**

## 1. Install the app

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/sivajyothis7/warehouse_3pl.git --branch develop
bench --site your-site.localhost install-app warehouse_3pl
bench --site your-site.localhost migrate
bench build --app warehouse_3pl
```

The `after_install` hook adds the custom fields required on ERPNext doctypes
(Customer, Warehouse, Item, Batch, Stock Entry, Delivery Note, Invoices).

## 2. Set up one client

1. Open **Customer** in Desk and create a new customer (e.g. "Acme Goods").
2. Check **Is 3PL Client** and set the **Client Code** (e.g. `ACME`).
3. Assign a **Default Temperature Zone** if you run mixed-temperature storage.
4. Attach an **Active Rate Card** — see [Rate Cards](/reference/billing/).

## 3. Configure warehouses as bins

Each physical bin is a Frappe **Warehouse** record. The app adds bin-level
attributes:

| Field | Purpose |
|---|---|
| `temperature_zone` | Ambient / Chilled / Frozen |
| `zone_type` | Receiving / Storage / Picking / Staging |
| `aisle` / `rack` / `level` | Physical address |
| `bin_code` | Short label used on labels and scanners |
| Capacity fields | Volume / weight limits for putaway suggestions |

## 4. Take a job end-to-end

The quickest way to verify the install is to run one job through the full
flow. Follow the walkthrough in [End-to-End Flow](/guide/end-to-end-flow/).

At a glance:

```
ASN → Receiving → Putaway Task → Stock Entry (auto)
Client Order → Wave → Pick Task → Pack Task → Delivery Note (auto)
All activities → Billing Transaction (auto)
```

## Next steps

- Read [How it works](/user/overview/) for a conceptual tour.
- Read [Architecture](/guide/architecture/) for the developer's view.
- Configure [Inventory Policies](/reference/policy-engine/) to tune allocation.
