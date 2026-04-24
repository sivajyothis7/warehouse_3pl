---
title: Doctypes
description: The 26 doctypes that make up Warehouse 3PL, grouped by role.
---

Warehouse 3PL defines **26 doctypes**. They fall into four groups:
operational flow, configuration, central hub, and tracking children.

## Operational — Inbound

| Doctype | Role | Key methods |
|---|---|---|
| **ASN** | Advance shipment notice from client. | `make_receiving()` |
| **ASN Line** (child) | One expected SKU line. | — |
| **Receiving** | Actual goods receipt at the dock. | submit triggers Putaway Task generation |
| **Receiving Line** (child) | One received SKU line. | — |
| **Putaway Task** | Move from receiving staging to a storage bin. | `complete_putaway()` |

## Operational — Outbound

| Doctype | Role | Key methods |
|---|---|---|
| **Client Order** | Client fulfillment request. | — |
| **Client Order Line** (child) | One ordered SKU. | — |
| **Wave** | Grouped picking round. | `release_wave()` |
| **Wave Order** (child) | Order membership in a wave. | — |
| **Pick Task** | One picker's walk. | `start_pick()`, `complete_pick()` |
| **Pick Task Line** (child) | One bin → qty → batch pick. | — |
| **Pack Task** | Cartonising + carrier handoff. | `complete_pack()` |
| **Pack Task Line** (child) | One carton's contents. | — |

## Configuration

| Doctype | Role |
|---|---|
| **Client Item** | Maps a client's SKU to an internal Item. |
| **Warehouse Location** | Bin-level storage record (volume, capacity, zone). |
| **Inventory Policy** | Rules for allocation, putaway, QC. |
| **Rate Card** | Per-client price book. |
| **Rate Card Line** (child) | Individual priced activity line. |

## Central hub

| Doctype | Role |
|---|---|
| **Warehouse Job Record** | Ties every operation, movement and voucher together per job. |

Its children (all `Job ...` doctypes) are:

| Child table | Holds |
|---|---|
| **Job Operational Info** | Task references and timings. |
| **Job Stock Movement** | Stock Entry references. |
| **Job Storage Info** | Bin assignments. |
| **Job Vehicle Info** | Inbound/outbound vehicles + BOLs. |
| **Job Voucher** | Related SI / PI / JE (including drafts). |

## Tracking

| Doctype | Role |
|---|---|
| **Billing Transaction** | One activity × unit × rate, awaiting or invoiced. |

## Whitelisted methods cheat-sheet

These are the methods backing the action buttons on the forms:

| Doctype | Method | Effect |
|---|---|---|
| ASN | `make_receiving` | Clones an ASN into a new Receiving via `get_mapped_doc`. |
| Pick Task | `start_pick` | Stamps a start time and moves status to `In Progress`. |
| Pick Task | `complete_pick` | Closes picks and auto-creates a Pack Task. |
| Pack Task | `complete_pack` | Creates an ERPNext Delivery Note. |
| Putaway Task | `complete_putaway` | Creates a zero-value Stock Entry. |
| Wave | `release_wave` | Generates Pick Tasks for all orders in the wave. |
| Warehouse Job Record | `get_job_dashboard_data` | Dashboard API for stock summary + P&L. |

## Naming conventions

- Child tables are named `{Parent} Line` (e.g. `Receiving Line`).
- Status fields are `options`-constrained in the doctype JSON.
- When using `get_mapped_doc`, status fields go in `field_no_map` to avoid
  mis-mapping.
- Every operational doc has a `warehouse_job` Link that points back to the
  central Warehouse Job Record.
