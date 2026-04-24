import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, today


class DemoWorkflowGenerator(Document):
    def validate(self):
        if self.item_count and self.item_count < 1:
            frappe.throw("Number of Demo Items must be at least 1")
        if self.qty_per_item and self.qty_per_item <= 0:
            frappe.throw("Receive Qty per Item must be greater than 0")
        if self.order_qty and self.qty_per_item and self.order_qty > self.qty_per_item:
            frappe.throw("Order Qty per Item cannot exceed Receive Qty per Item")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

@frappe.whitelist()
def run_demo():
    settings = frappe.get_single("Demo Workflow Generator")
    runner = DemoRunner(settings)
    return runner.run()


class DemoRunner:
    """Drives the full 3PL pipeline end-to-end from one Single doctype form."""

    def __init__(self, settings):
        self.settings = settings
        self.log_lines = []
        self.created = {
            "customer": None,
            "items": [],
            "warehouses": [],
            "rate_card": None,
            "asn": None,
            "receiving": None,
            "putaway_tasks": [],
            "client_order": None,
            "wave": None,
            "pick_task": None,
            "pack_task": None,
            "delivery_note": None,
        }

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(self):
        try:
            self._log("Starting demo workflow run")
            self._resolve_company()
            self._ensure_customer()
            self._ensure_items()
            self._ensure_warehouses()
            if self.settings.create_rate_card:
                self._ensure_rate_card()
            self._run_inbound()
            self._run_outbound()
            self._save_log(status="Success")
            frappe.db.commit()
            self._log("Demo workflow complete")
            return {"ok": True, "log": "\n".join(self.log_lines), "created": self.created}
        except Exception as exc:
            frappe.db.rollback()
            self._log(f"ERROR: {exc}")
            self._save_log(status="Failed")
            frappe.db.commit()
            frappe.log_error(frappe.get_traceback(), "Demo Workflow Generator")
            raise

    # ------------------------------------------------------------------
    # Setup: company / masters
    # ------------------------------------------------------------------

    def _resolve_company(self):
        company = self.settings.company or frappe.db.get_single_value(
            "Global Defaults", "default_company"
        )
        if not company:
            first = frappe.get_all("Company", limit=1, pluck="name")
            company = first[0] if first else None
        if not company:
            frappe.throw("No Company found. Create a Company in ERPNext before running the demo.")
        self.company = company
        self.company_abbr = frappe.db.get_value("Company", company, "abbr")
        self._log(f"Using company: {company} ({self.company_abbr})")

    def _ensure_customer(self):
        name = self.settings.client_name
        if not frappe.db.exists("Customer", name):
            doc = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": name,
                "customer_type": "Company",
                "customer_group": self._default("Customer Group", "All Customer Groups"),
                "territory": self._default("Territory", "All Territories"),
                "is_3pl_client": 1,
                "client_code": self.settings.client_code,
                "default_temp_zone": self.settings.default_temp_zone or "Ambient",
            })
            doc.insert(ignore_permissions=True)
            self._log(f"Created Customer: {doc.name}")
        else:
            doc = frappe.get_doc("Customer", name)
            changed = False
            if not doc.is_3pl_client:
                doc.is_3pl_client = 1
                changed = True
            if not doc.client_code:
                doc.client_code = self.settings.client_code
                changed = True
            if not doc.default_temp_zone:
                doc.default_temp_zone = self.settings.default_temp_zone or "Ambient"
                changed = True
            if changed:
                doc.save(ignore_permissions=True)
                self._log(f"Updated Customer: {doc.name}")
            else:
                self._log(f"Reusing Customer: {doc.name}")
        self.created["customer"] = doc.name
        self.customer = doc.name

    def _ensure_items(self):
        group = self._default("Item Group", "All Item Groups")
        uom = self._default("UOM", "Nos")
        for idx in range(1, int(self.settings.item_count) + 1):
            code = f"DEMO-SKU-{idx:03d}"
            if not frappe.db.exists("Item", code):
                item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": code,
                    "item_name": f"Demo Widget {idx}",
                    "item_group": group,
                    "stock_uom": uom,
                    "is_stock_item": 1,
                    "include_item_in_manufacturing": 0,
                    "storage_temp_zone": self.settings.default_temp_zone or "Ambient",
                })
                item.insert(ignore_permissions=True)
                self._log(f"Created Item: {code}")
            else:
                self._log(f"Reusing Item: {code}")
            self.created["items"].append(code)

    def _ensure_warehouses(self):
        staging = self.settings.staging_warehouse
        target = self.settings.target_warehouse
        if not staging:
            staging = self._ensure_warehouse(
                name_base="Demo Staging",
                zone_type="Receiving",
            )
        if not target:
            target = self._ensure_warehouse(
                name_base="Demo Bin A-01",
                zone_type="Storage",
            )
        self.staging_warehouse = staging
        self.target_warehouse = target
        self.created["warehouses"] = [staging, target]
        self._log(f"Staging: {staging}; Target: {target}")

    def _ensure_warehouse(self, name_base, zone_type):
        full_name = f"{name_base} - {self.company_abbr}"
        if frappe.db.exists("Warehouse", full_name):
            return full_name
        parent = frappe.db.get_value(
            "Warehouse",
            {"company": self.company, "is_group": 1},
            "name",
            order_by="creation asc",
        )
        doc = frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": name_base,
            "company": self.company,
            "is_group": 0,
            "parent_warehouse": parent,
            "temperature_zone": self.settings.default_temp_zone or "Ambient",
            "zone_type": zone_type,
        })
        doc.insert(ignore_permissions=True)
        self._log(f"Created Warehouse: {doc.name}")
        return doc.name

    def _ensure_rate_card(self):
        existing = frappe.db.get_value(
            "Rate Card",
            {"client": self.customer, "status": "Active"},
            "name",
        )
        if existing:
            self._log(f"Reusing Rate Card: {existing}")
            self.created["rate_card"] = existing
            return
        rc = frappe.get_doc({
            "doctype": "Rate Card",
            "client": self.customer,
            "effective_from": today(),
            "status": "Active",
            "rate_lines": [
                {"activity_type": "Receiving", "uom": "Per Unit",
                 "rate": self.settings.receiving_rate or 0.50},
                {"activity_type": "Picking", "uom": "Per Unit",
                 "rate": self.settings.picking_rate or 0.60},
                {"activity_type": "Packing", "uom": "Per Unit",
                 "rate": self.settings.packing_rate or 0.40},
                {"activity_type": "Shipping", "uom": "Per Order",
                 "rate": self.settings.shipping_rate or 5.00},
            ],
        })
        rc.insert(ignore_permissions=True)
        self._log(f"Created Rate Card: {rc.name}")
        self.created["rate_card"] = rc.name

    # ------------------------------------------------------------------
    # Inbound: ASN → Receiving → Putaway
    # ------------------------------------------------------------------

    def _run_inbound(self):
        self._log("--- Inbound ---")
        asn = frappe.get_doc({
            "doctype": "ASN",
            "client": self.customer,
            "expected_date": today(),
            "supplier_ref": "DEMO-SHIPMENT-001",
            "notes": "Auto-generated by Demo Workflow Generator",
            "items": [
                {
                    "item_code": code,
                    "expected_qty": self.settings.qty_per_item,
                    "uom": "Nos",
                    "lot_no": f"LOT-{code}-A",
                }
                for code in self.created["items"]
            ],
        })
        asn.insert(ignore_permissions=True)
        asn.submit()
        self.created["asn"] = asn.name
        self._log(f"Submitted ASN: {asn.name}")

        from warehouse_3pl.warehouse_3pl.doctype.asn.asn import make_receiving

        rcv_doc = make_receiving(asn.name)
        rcv_doc.receiving_date = today()
        rcv_doc.staging_location = self.staging_warehouse
        rcv_doc.insert(ignore_permissions=True)
        rcv_doc.submit()
        self.created["receiving"] = rcv_doc.name
        self._log(f"Submitted Receiving: {rcv_doc.name}")

        tasks = frappe.get_all(
            "Putaway Task",
            filters={"receiving_ref": rcv_doc.name},
            pluck="name",
        )
        from warehouse_3pl.warehouse_3pl.doctype.putaway_task.putaway_task import (
            complete_putaway,
        )
        for task_name in tasks:
            frappe.db.set_value("Putaway Task", task_name, "target_location", self.target_warehouse)
            complete_putaway(task_name)
            self._log(f"Completed Putaway: {task_name}")
        self.created["putaway_tasks"] = tasks

    # ------------------------------------------------------------------
    # Outbound: Client Order → Wave → Pick → Pack → Delivery Note
    # ------------------------------------------------------------------

    def _run_outbound(self):
        self._log("--- Outbound ---")
        co = frappe.get_doc({
            "doctype": "Client Order",
            "client": self.customer,
            "order_date": today(),
            "priority": "Normal",
            "client_ref": "DEMO-PO-001",
            "items": [
                {
                    "item_code": code,
                    "qty": self.settings.order_qty,
                    "uom": "Nos",
                }
                for code in self.created["items"]
            ],
        })
        co.insert(ignore_permissions=True)
        co.submit()
        self.created["client_order"] = co.name
        self._log(f"Submitted Client Order: {co.name} (status={co.status})")

        wave = frappe.get_doc({
            "doctype": "Wave",
            "wave_date": today(),
            "picking_strategy": "Single Order",
            "status": "Planning",
            "orders": [{"client_order": co.name}],
        })
        wave.insert(ignore_permissions=True)
        self.created["wave"] = wave.name
        self._log(f"Created Wave: {wave.name}")

        from warehouse_3pl.warehouse_3pl.doctype.wave.wave import release_wave
        release_wave(wave.name)
        self._log(f"Released Wave: {wave.name}")

        pick_name = frappe.db.get_value(
            "Pick Task",
            {"wave": wave.name, "client_order": co.name},
            "name",
        )
        if not pick_name:
            frappe.throw(f"Wave {wave.name} released but no Pick Task was created — "
                         "check stock allocation for the demo items.")
        self.created["pick_task"] = pick_name
        self._log(f"Pick Task created: {pick_name}")

        from warehouse_3pl.warehouse_3pl.doctype.pick_task.pick_task import (
            start_pick, complete_pick,
        )
        start_pick(pick_name)
        complete_pick(pick_name)
        self._log(f"Completed Pick: {pick_name}")

        pack_name = frappe.db.get_value("Pack Task", {"pick_task": pick_name}, "name")
        if not pack_name:
            frappe.throw(f"Pack Task was not created for Pick Task {pick_name}.")
        self.created["pack_task"] = pack_name
        self._log(f"Pack Task created: {pack_name}")

        from warehouse_3pl.warehouse_3pl.doctype.pack_task.pack_task import complete_pack
        complete_pack(pack_name)
        dn_name = frappe.db.get_value("Pack Task", pack_name, "delivery_note")
        self.created["delivery_note"] = dn_name
        self._log(f"Completed Pack: {pack_name}, Delivery Note: {dn_name}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _default(self, doctype, fallback):
        """Return the first-ordered name of a master doctype, falling back to `fallback`."""
        if frappe.db.exists(doctype, fallback):
            return fallback
        first = frappe.get_all(doctype, limit=1, order_by="creation asc", pluck="name")
        return first[0] if first else fallback

    def _log(self, line):
        stamp = frappe.utils.now()
        self.log_lines.append(f"[{stamp}] {line}")

    def _save_log(self, status):
        self.settings.db_set({
            "last_run_status": status,
            "last_run_at": now_datetime(),
            "last_run_log": "\n".join(self.log_lines),
        }, update_modified=False)
