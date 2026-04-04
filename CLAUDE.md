# Warehouse 3PL - Agent Context

## What This Is

A **3PL (Third-Party Logistics) Warehouse Management System** built as a custom Frappe/ERPNext v15 app. It manages the full lifecycle of warehouse operations for clients who outsource their warehousing — receiving, storage, picking, packing, shipping, and billing.

**Key concept:** This is a *bailee* system — the warehouse operator holds goods on behalf of clients. The warehouse never "owns" the inventory. All stock entries use zero-value accounting.

## Tech Stack

- **Framework:** Frappe v15 (Python + MariaDB + Redis)
- **ERP:** ERPNext v15 (Stock, Accounts modules)
- **Python:** 3.10+
- **Frontend:** Frappe Desk (server-rendered JS forms, not React/Vue)
- **Build:** flit (pyproject.toml), esbuild for JS

## Bench & Site Setup

```
Bench path:   /Users/sayanthns/frappe-bench
Site:         warehouse.localhost
Default port: 8000
DB type:      MariaDB
```

### Starting the Server

```bash
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
cd /Users/sayanthns/frappe-bench

# Kill stale redis first (common issue)
pkill -9 -f redis-server 2>/dev/null; sleep 2

# Start
bench start
```

### Multi-Site Routing

This bench has multiple sites. Each site has `host_name` in its `site_config.json` for hostname-based routing:
- `warehouse.localhost:8000` → warehouse_3pl site
- `cooperheats.localhost:8000` → cooperheats site

**Known issue:** `default_site` in `common_site_config.json` can get overwritten by bench commands. The `host_name` config makes this harmless, but if things break, check:
```bash
python3 -c "import json; print(json.load(open('sites/common_site_config.json'))['default_site'])"
```
If wrong, fix with:
```bash
bench use warehouse.localhost
```

## Architecture

### Doctype Hierarchy (26 doctypes)

```
Warehouse Job Record (central hub — links everything)
├── Inbound
│   ├── ASN (Advance Shipment Notice) → ASN Line (child)
│   ├── Receiving → Receiving Line (child)
│   └── Putaway Task
├── Outbound
│   ├── Client Order → Client Order Line (child)
│   ├── Wave → Wave Order (child)
│   ├── Pick Task → Pick Task Line (child)
│   └── Pack Task → Pack Task Line (child)
├── Configuration
│   ├── Client Item (client-specific SKU mapping)
│   ├── Warehouse Location (bin-level storage)
│   ├── Inventory Policy (FIFO/FEFO rules)
│   └── Rate Card → Rate Card Line (child, pricing)
├── Tracking
│   ├── Billing Transaction
│   ├── Job Operational Info (child)
│   ├── Job Stock Movement (child)
│   ├── Job Storage Info (child)
│   ├── Job Vehicle Info (child)
│   └── Job Voucher (child)
```

### Document Flow

```
ASN → Receiving → Putaway Task → Stock Entry (auto)
Client Order → Wave → Pick Task → Pack Task → Delivery Note (auto)
All operations → Billing Transaction (auto via billing.py)
```

### Key Whitelisted Methods

| Doctype | Method | What It Does |
|---------|--------|-------------|
| ASN | `make_receiving()` | Creates Receiving from ASN via `get_mapped_doc` |
| Pick Task | `start_pick()`, `complete_pick()` | Lifecycle + auto-creates Pack Task |
| Pack Task | `complete_pack()` | Auto-creates ERPNext Delivery Note |
| Putaway Task | `complete_putaway()` | Auto-creates ERPNext Stock Entry |
| Wave | `release_wave()` | Creates Pick Tasks for all orders in wave |
| Warehouse Job Record | `get_job_dashboard_data()` | Dashboard API for job stats |

### Utility Engines (in `utils/`)

| Module | Purpose |
|--------|---------|
| `allocation_engine.py` | FIFO/FEFO stock allocation from bins |
| `policy_engine.py` | Resolves inventory policy by client → item group → zone |
| `putaway_engine.py` | Suggests bin placement based on zone/capacity |
| `billing.py` | Creates Billing Transactions from warehouse activities |

### Custom Fields on ERPNext Doctypes

Defined in `warehouse_3pl/custom_fields/setup.py`, added via `after_install` hook:

- **Customer:** `is_3pl_client`, `client_code`, `default_temp_zone`, `active_rate_card`
- **Warehouse:** `temperature_zone`, `zone_type`, `aisle`, `rack`, `level`, `bin_code`, capacity fields
- **Item:** `storage_temp_zone`, `hazmat_class`, `lot_tracking`, `velocity_class`
- **Batch:** `supplier_lot`, `receiving_date`, `country_of_origin`, `qc_status`
- **Stock Entry:** `client`, `warehouse_job`, `asn`
- **Delivery Note:** `client`, `warehouse_job`, `carrier`, `tracking_number`, `wave`, `bol_number`
- **Sales/Purchase Invoice:** `warehouse_job`

## Common Tasks

### Run Migrate After Changes

```bash
cd /Users/sayanthns/frappe-bench
bench --site warehouse.localhost migrate
bench build --app warehouse_3pl
```

### Create a New Doctype

```bash
bench --site warehouse.localhost new-doctype "Doctype Name" --module "Warehouse 3PL"
```
Then define fields in the JSON, add Python controller logic, and run `bench migrate`.

### Run Tests

```bash
bench --site warehouse.localhost run-tests --app warehouse_3pl
# Or specific:
bench --site warehouse.localhost run-tests --module "warehouse_3pl.warehouse_3pl.utils.test_allocation_engine"
```

### Access the Console

```bash
bench --site warehouse.localhost console
```
```python
import frappe
frappe.get_all("ASN", filters={"status": "Confirmed"}, fields=["name", "client"])
```

## Code Conventions

- **Python:** Follows ruff linter rules (configured in pyproject.toml), line length 110
- **JS:** Frappe client script pattern — `frappe.ui.form.on('Doctype', { ... })`
- **Status fields:** Always use `options` in doctype JSON, check with `field_no_map` when using `get_mapped_doc`
- **Child tables:** Named `{Parent} Line` (e.g., ASN Line, Receiving Line)
- **Links:** All operational docs link back to `warehouse_job` (the central hub)
- **Workspace:** Both `content` (JSON string with block definitions) AND `links` (array) must be updated — content controls rendering

## What's Built vs. What's Pending

### Built (Working)
- All 26 doctypes with full CRUD
- Inbound flow: ASN → Receiving → Putaway → Stock Entry
- Outbound flow: Client Order → Wave → Pick → Pack → Delivery Note
- Warehouse Job Record dashboard with stock summary and P&L
- Custom fields on ERPNext doctypes
- Workspace with 7 card sections and 9 shortcuts
- Utility engines (allocation, policy, putaway, billing)
- Unit tests for engines

### Pending / Not Yet Built
- **Billing Engine scheduler** — auto-generate billing from warehouse events on schedule
- **Cold Chain module** — temperature monitoring and compliance
- **Client Portal** — external client web portal for order/status visibility
- **Enhanced Desk UI polish** — remaining form beautification
- **Role-based permissions** — granular per-role access control
- **API for external integrations** — REST API for WMS/TMS systems

## Documentation

Live docs site: https://warehouse-3pl-docs.vercel.app
Repo: https://github.com/sayanthns/warehouse-3pl-docs

Built with VitePress + Mermaid diagrams. Covers both user guides and developer/architecture guides.
