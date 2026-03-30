import frappe
from frappe.model.document import Document


class InventoryPolicy(Document):
    def validate(self):
        self.validate_qc_sampling()
        self.validate_shelf_life()

    def validate_qc_sampling(self):
        if self.qc_required and not self.qc_sampling_pct:
            frappe.throw("QC Sampling % is required when QC is enabled")
        if self.qc_sampling_pct and (self.qc_sampling_pct < 0 or self.qc_sampling_pct > 100):
            frappe.throw("QC Sampling % must be between 0 and 100")

    def validate_shelf_life(self):
        if self.min_remaining_shelf_life_pct and (
            self.min_remaining_shelf_life_pct < 0 or self.min_remaining_shelf_life_pct > 100
        ):
            frappe.throw("Min Remaining Shelf Life % must be between 0 and 100")
