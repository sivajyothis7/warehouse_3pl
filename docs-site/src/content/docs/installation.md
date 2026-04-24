---
title: Installation
description: Install Warehouse 3PL on a fresh Frappe/ERPNext v15 bench.
---

Warehouse 3PL is a custom Frappe app. It is installed the same way as any
other Frappe app, on top of an existing ERPNext v15 bench.

## Bench prerequisites

Make sure the bench already has ERPNext v15 installed:

```bash
bench version
# frappe 15.x.x
# erpnext 15.x.x
```

If not, install ERPNext first:

```bash
bench get-app --branch version-15 erpnext
bench --site your-site install-app erpnext
```

## Install Warehouse 3PL

```bash
cd $PATH_TO_YOUR_BENCH

# 1. Fetch the app
bench get-app https://github.com/sivajyothis7/warehouse_3pl.git --branch develop

# 2. Install it on the site
bench --site your-site.localhost install-app warehouse_3pl

# 3. Run migrations (creates the 26 doctypes + custom fields)
bench --site your-site.localhost migrate

# 4. Build assets
bench build --app warehouse_3pl
```

## Verify the install

After install, open **Desk** and confirm:

- The **Warehouse 3PL** workspace exists in the sidebar.
- The **Customer** form has an **Is 3PL Client** checkbox.
- The **Warehouse** form has fields for `temperature_zone`, `bin_code`, etc.
- The doctype list shows: ASN, Receiving, Putaway Task, Client Order, Wave,
  Pick Task, Pack Task, Warehouse Job Record, Rate Card, Inventory Policy,
  Billing Transaction, Warehouse Location, Client Item.

## Upgrade

```bash
cd $PATH_TO_YOUR_BENCH/apps/warehouse_3pl
git pull
cd $PATH_TO_YOUR_BENCH
bench --site your-site.localhost migrate
bench build --app warehouse_3pl
bench restart
```

## Uninstall

```bash
bench --site your-site.localhost uninstall-app warehouse_3pl
bench remove-app warehouse_3pl
```

:::caution
Uninstalling removes the custom fields added to ERPNext doctypes. If you have
operational data referencing those fields, back it up first.
:::

## Development install

If you're customising the app:

```bash
cd apps/warehouse_3pl
pre-commit install
```

Tooling: `ruff`, `eslint`, `prettier`, `pyupgrade`. See
[Customisation](/guide/customisation/) for the extension points.
