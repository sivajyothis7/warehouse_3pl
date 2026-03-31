import frappe
from frappe.model.document import Document
from frappe.utils import today


class PackTask(Document):
    def validate(self):
        if not self.items:
            frappe.throw("At least one pack line is required")

    def complete(self):
        if self.status == "Complete":
            frappe.throw("Pack Task is already complete")
        self._create_delivery_note()
        self._log_billing()
        self.db_set("status", "Complete")
        if self.client_order:
            frappe.db.set_value("Client Order", self.client_order, "status", "Shipped")

    def _create_delivery_note(self):
        company = frappe.db.get_single_value("Global Defaults", "default_company")
        if not company:
            company = frappe.get_all("Company", limit=1)[0].name

        # Find warehouse with stock
        source_warehouse = None
        if self.pick_task:
            # Try to get from pick task items
            pick_items = frappe.get_all(
                "Pick Task Line",
                filters={"parent": self.pick_task},
                fields=["from_location"],
                limit=1,
            )
            if pick_items:
                source_warehouse = pick_items[0].from_location

        if not source_warehouse:
            source_warehouse = frappe.db.get_value(
                "Bin",
                {"item_code": self.items[0].item_code, "actual_qty": (">", 0)},
                "warehouse",
            )

        if not source_warehouse:
            frappe.throw("No source warehouse found for delivery")

        dn = frappe.get_doc({
            "doctype": "Delivery Note",
            "customer": self.client,
            "company": company,
            "posting_date": today(),
            "client": self.client,
            "items": [],
        })
        for row in self.items:
            dn.append("items", {
                "item_code": row.item_code,
                "qty": row.qty,
                "warehouse": source_warehouse,
                "rate": 0,
                "allow_zero_valuation_rate": 1,
            })
        dn.insert(ignore_permissions=True)
        dn.submit()
        self.db_set("delivery_note", dn.name)

    def _log_billing(self):
        from warehouse_3pl.warehouse_3pl.utils.billing import create_billing_transaction

        total_packed = sum(row.qty for row in self.items)
        if total_packed > 0:
            create_billing_transaction(
                client=self.client,
                activity_type="Packing",
                qty=total_packed,
                source_doctype="Pack Task",
                source_name=self.name,
                uom="Per Unit",
            )
        create_billing_transaction(
            client=self.client,
            activity_type="Shipping",
            qty=1,
            source_doctype="Pack Task",
            source_name=self.name,
            uom="Per Order",
        )
