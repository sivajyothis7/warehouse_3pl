---
title: Custom Fields
description: The full list of ERPNext custom fields added by Warehouse 3PL.
---

All custom fields are defined in `warehouse_3pl/custom_fields/setup.py`
and are attached on install by the `after_install` hook.

## Customer

| Field | Type | Purpose |
|---|---|---|
| `is_3pl_client` | Check | Flag — turns on 3PL UI and filters. |
| `client_code` | Data | Short code used on labels and Client Items. |
| `default_temp_zone` | Link | Default storage zone. |
| `active_rate_card` | Link | Rate Card the billing engine resolves against. |

## Warehouse

| Field | Type | Purpose |
|---|---|---|
| `temperature_zone` | Link | Ambient / Chilled / Frozen. |
| `zone_type` | Select | Receiving / Storage / Picking / Staging. |
| `aisle` | Data | Aisle label. |
| `rack` | Data | Rack label. |
| `level` | Data | Vertical level. |
| `bin_code` | Data | Short bin label. |
| `max_volume_cbm` | Float | Volume capacity. |
| `max_weight_kg` | Float | Weight capacity. |
| `velocity_class` | Select | A / B / C for forward-pick placement. |

## Item

| Field | Type | Purpose |
|---|---|---|
| `storage_temp_zone` | Link | Zone the item must be stored in. |
| `hazmat_class` | Data | Classification for hazmat handling. |
| `lot_tracking` | Check | Enable batch tracking and FEFO. |
| `velocity_class` | Select | A / B / C for putaway ranking. |

## Batch

| Field | Type | Purpose |
|---|---|---|
| `supplier_lot` | Data | Vendor lot reference. |
| `receiving_date` | Date | Used by FIFO allocation. |
| `country_of_origin` | Link | Customs and compliance. |
| `qc_status` | Select | Pending / Passed / Held / Rejected. |

## Stock Entry

| Field | Type | Purpose |
|---|---|---|
| `client` | Link | Customer this movement is for. |
| `warehouse_job` | Link | Back-link to the Warehouse Job Record. |
| `asn` | Link | Originating ASN (for inbound moves). |

## Delivery Note

| Field | Type | Purpose |
|---|---|---|
| `client` | Link | Customer. |
| `warehouse_job` | Link | Back-link to the Warehouse Job Record. |
| `carrier` | Data | Carrier name. |
| `tracking_number` | Data | Carrier tracking reference. |
| `wave` | Link | Source Wave. |
| `bol_number` | Data | Bill of Lading. |

## Sales Invoice & Purchase Invoice

| Field | Type | Purpose |
|---|---|---|
| `warehouse_job` | Link | Back-link to the Warehouse Job Record — used by the live P&L roll-up. |

## Installing / refreshing on an existing site

```bash
bench --site your-site.localhost execute \
  warehouse_3pl.custom_fields.setup.execute
```

Safe to re-run — the helper is idempotent.
