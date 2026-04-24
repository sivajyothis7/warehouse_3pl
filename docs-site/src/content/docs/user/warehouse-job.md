---
title: Warehouse Job Record
description: The central hub doc that ties an entire job's operations, stock movements and billing together.
---

The **Warehouse Job Record** (WJR) is the single pane of glass for one
logical job — whether it's one ASN through to putaway, or one order from
pick to delivery. If you only look at one document per day, look at this.

## What it links

Every operational doctype carries a `warehouse_job` field. The WJR collects
them back into one place through **child tables**:

| Child table | What it holds |
|---|---|
| **Job Operational Info** | Pick/Pack/Putaway task references and timings. |
| **Job Stock Movement** | Every Stock Entry raised for this job. |
| **Job Storage Info** | Bin assignments and occupancy deltas. |
| **Job Vehicle Info** | Inbound / outbound vehicle details, BOLs. |
| **Job Voucher** | Related SI / PI / JE (including drafts). |

## The dashboard

The header of the WJR calls
`Warehouse Job Record.get_job_dashboard_data()` to render a live panel:

- **Stock summary** — items in / items out, by zone.
- **Live P&L** — revenue from Billing Transactions minus cost entries from
  linked Purchase Invoices and Journal Entries. Draft SI/PI/JE are
  included, so supervisors see the picture before month-end.
- **Status roll-up** — the worst status across linked operations.

## Why it exists

Without the WJR, operational data splinters across five or more doctypes
and finance can't reconcile a job. The WJR:

1. Gives ops a single link to share when something goes wrong ("see
   WJR-00231").
2. Gives finance a ready-made group-by key for job-level P&L.
3. Gives engineering an obvious place to hang new tracking fields without
   polluting ERPNext core tables.

## Finding jobs in Desk

- Filter by `client` and `status` from the list view.
- Use the workspace shortcut **"Open Jobs Today"**.
- From any ASN, Pick Task, Delivery Note, etc., click the **Warehouse Job**
  link in the header.
