import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class PutawayTask(Document):
    def validate(self):
        if self.qty <= 0:
            frappe.throw("Quantity must be greater than 0")
        if self.source_location == self.target_location:
            frappe.msgprint("Source and target locations are the same — no transfer needed",
                            indicator="orange", alert=True)

    def complete(self):
        """Mark the putaway task as complete and create a Material Transfer Stock Entry."""
        if self.status == "Complete":
            frappe.throw("Putaway Task is already complete")
        self._create_transfer_stock_entry()
        self.db_set("status", "Complete")
        self.db_set("completed_at", now_datetime())

    def _create_transfer_stock_entry(self):
        if self.source_location == self.target_location:
            return
        company = frappe.db.get_value("Warehouse", self.source_location, "company")
        if not company:
            company = frappe.db.get_single_value("Global Defaults", "default_company")
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "company": company,
            "client": self.client,
            "reason_code": "Putaway",
            "items": [{
                "item_code": self.item_code,
                "qty": self.qty,
                "s_warehouse": self.source_location,
                "t_warehouse": self.target_location,
                "allow_zero_valuation_rate": 1,
            }],
        })
        se.insert(ignore_permissions=True)
        se.submit()
        self.db_set("stock_entry", se.name)
