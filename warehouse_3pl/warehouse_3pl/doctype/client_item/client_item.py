import frappe
from frappe.model.document import Document


class ClientItem(Document):
    def validate(self):
        self.validate_client_is_3pl()

    def validate_client_is_3pl(self):
        is_3pl = frappe.db.get_value("Customer", self.client, "is_3pl_client")
        if not is_3pl:
            frappe.throw(f"Customer {self.client} is not a 3PL client")
