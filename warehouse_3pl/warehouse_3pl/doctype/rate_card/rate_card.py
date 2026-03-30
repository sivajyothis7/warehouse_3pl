import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class RateCard(Document):
    def validate(self):
        self.validate_dates()
        self.validate_duplicate_activities()

    def validate_dates(self):
        if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
            frappe.throw("Effective To date cannot be before Effective From date")

    def validate_duplicate_activities(self):
        seen = set()
        for line in self.rate_lines:
            key = (line.activity_type, line.uom)
            if key in seen:
                frappe.throw(f"Duplicate activity: {line.activity_type} ({line.uom}) appears more than once")
            seen.add(key)


def get_rate(client, activity_type, uom=None):
    """Get the active rate for a client and activity type."""
    today = frappe.utils.today()
    rate_card_name = frappe.db.get_value(
        "Rate Card",
        {"client": client, "status": "Active", "effective_from": ("<=", today)},
        "name",
        order_by="effective_from desc",
    )
    if not rate_card_name:
        return 0, 0
    filters = {"parent": rate_card_name, "activity_type": activity_type}
    if uom:
        filters["uom"] = uom
    line = frappe.db.get_value("Rate Card Line", filters, ["rate", "minimum_charge"], as_dict=True)
    if line:
        return line.rate or 0, line.minimum_charge or 0
    return 0, 0
