---
title: Customisation
description: Extending Warehouse 3PL — custom fields, hooks, client scripts, and the workspace.
---

Warehouse 3PL is designed to be extended without forking ERPNext. This
page lists the extension points and the conventions the app itself
follows.

## Adding a custom field

All custom fields added by the app live in
`warehouse_3pl/custom_fields/setup.py` and are installed by the
`after_install` hook. To add your own:

1. Append your field to the module-level dict in `setup.py`.
2. Run the installer helper on upgrade:

```bash
bench --site your-site.localhost execute \
  warehouse_3pl.custom_fields.setup.execute
```

See [Custom Fields](/reference/custom-fields/) for the current list.

## Adding a new doctype

```bash
bench --site your-site.localhost new-doctype "My New Doctype" \
  --module "Warehouse 3PL"
```

Then:

1. Edit the generated JSON to define fields.
2. Add Python controller logic in the generated `.py` file.
3. Add `warehouse_job` as a Link field if the doctype is operational so
   it rolls up onto the Warehouse Job Record.
4. Run `bench migrate` and `bench build --app warehouse_3pl`.

## Adding a Client Script / form button

Frappe client scripts use the canonical pattern:

```js
frappe.ui.form.on("Pick Task", {
  refresh(frm) {
    if (frm.doc.status === "In Progress") {
      frm.add_custom_button(__("Complete Pick"), () => {
        frm.call("complete_pick").then(() => frm.reload_doc());
      });
    }
  },
});
```

When adding buttons that trigger server work, keep the logic on the
server (whitelisted method) and let the client just call it — that way the
same entry point is available to tests, the REST API, and the UI.

## Hooks

`warehouse_3pl/hooks.py` registers:

- `after_install` → attach custom fields.
- `doc_events` → minimal today. Use sparingly; prefer form buttons
  calling whitelisted methods so the intent is explicit.
- `scheduler_events` → currently empty. The roadmap adds a periodic
  billing sweep here.

## Workspace

The Desk workspace is defined in
`warehouse_3pl/workspace/warehouse_3pl.json`. Two fields must stay in
sync when you edit it:

- **`content`** — the JSON block layout (this controls rendering).
- **`links`** — the array of link/shortcut entries.

Editing one without the other usually produces a workspace that looks
fine in the builder but renders empty.

## Coding conventions

- **Python** — `ruff` with line length 110 (see `pyproject.toml`).
- **JS** — Frappe client-script pattern (`frappe.ui.form.on`).
- **Statuses** — always `Select` with an `options` list. Never compare
  statuses as free-form strings.
- **`get_mapped_doc`** — add status fields to `field_no_map` so the target
  doc picks up its default rather than inheriting the source's status.
- **Child tables** — named `{Parent} Line`.
- **Operational doctypes** — all link to `warehouse_job`.

## Pre-commit

```bash
cd apps/warehouse_3pl
pre-commit install
```

Tools: `ruff`, `eslint`, `prettier`, `pyupgrade`. The config lives in
`.pre-commit-config.yaml` at the app root.
