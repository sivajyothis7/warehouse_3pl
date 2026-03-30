import frappe
from frappe.model.document import Document


class WarehouseLocation(Document):
    def validate(self):
        self.validate_capacity()
        self.set_barcode_if_empty()

    def validate_capacity(self):
        if self.max_weight_kg and self.max_weight_kg < 0:
            frappe.throw("Max Weight cannot be negative")
        if self.max_volume_cbm and self.max_volume_cbm < 0:
            frappe.throw("Max Volume cannot be negative")

    def set_barcode_if_empty(self):
        if not self.barcode:
            self.barcode = f"{self.zone}-{self.aisle}-{self.rack}-{self.level}-{self.bin_code}"
