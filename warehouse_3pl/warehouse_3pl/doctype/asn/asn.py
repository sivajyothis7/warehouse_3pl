import frappe
from frappe.model.document import Document


class ASN(Document):
    def validate(self):
        self.validate_client_is_3pl()
        self.validate_items()

    def on_submit(self):
        self.db_set("status", "Confirmed")

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    def validate_client_is_3pl(self):
        is_3pl = frappe.db.get_value("Customer", self.client, "is_3pl_client")
        if not is_3pl:
            frappe.throw(f"Customer {self.client} is not a 3PL client")

    def validate_items(self):
        if not self.items:
            frappe.throw("At least one item line is required")
        for row in self.items:
            if row.expected_qty <= 0:
                frappe.throw(f"Row {row.idx}: Expected Qty must be greater than 0")
