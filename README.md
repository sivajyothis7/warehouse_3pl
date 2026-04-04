# Warehouse 3PL

A comprehensive **Third-Party Logistics (3PL) Warehouse Management System** built on [Frappe](https://frappeframework.com/) / [ERPNext](https://erpnext.com/) v15.

Manages the full lifecycle of warehouse operations for multiple clients: receiving, storage, picking, packing, shipping, and billing — all integrated with ERPNext's Stock and Accounting modules.

## Features

- **Inbound:** ASN (Advance Shipment Notice) → Receiving → Putaway with directed bin assignment
- **Outbound:** Client Order → Wave Planning → Pick Task → Pack Task → Delivery Note
- **Warehouse Job Record:** Central hub linking all operations, stock movements, and billing for a job
- **Inventory Policies:** Configurable FIFO/FEFO rotation, zone-based allocation
- **Multi-Client Billing:** Rate cards per client, automatic billing transaction logging
- **Custom Fields:** Extends ERPNext Customer, Warehouse, Item, Batch, Stock Entry, Delivery Note, and Invoice doctypes

## Requirements

- Python 3.10+
- Frappe v15
- ERPNext v15
- MariaDB 10.6+
- Redis 6+
- Node.js 18+

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/sayanthns/warehouse_3pl.git --branch develop
bench --site your-site.localhost install-app warehouse_3pl
bench --site your-site.localhost migrate
bench build --app warehouse_3pl
```

The `after_install` hook automatically creates custom fields on ERPNext doctypes.

## Module Structure

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
│   └── ... (child tables & tracking docs)
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

## Document Flow

```
INBOUND:   ASN → Receiving → Putaway Task → Stock Entry (auto-created)
OUTBOUND:  Client Order → Wave → Pick Task → Pack Task → Delivery Note (auto-created)
BILLING:   All activities → Billing Transaction (via Rate Card lookup)
TRACKING:  Everything links to → Warehouse Job Record
```

## Running Tests

```bash
bench --site your-site.localhost run-tests --app warehouse_3pl
```

## Documentation

Full user and developer documentation: **https://docs-site-brown-six.vercel.app**

- [User Guide](https://docs-site-brown-six.vercel.app/user/) — Step-by-step operations guide
- [Developer Guide](https://docs-site-brown-six.vercel.app/guide/overview) — Architecture and customization
- [End-to-End Flow](https://docs-site-brown-six.vercel.app/guide/end-to-end-flow) — Complete workflow with diagrams

## Contributing

This app uses `pre-commit` for code formatting and linting:

```bash
cd apps/warehouse_3pl
pre-commit install
```

Tools: ruff, eslint, prettier, pyupgrade

## License

MIT
