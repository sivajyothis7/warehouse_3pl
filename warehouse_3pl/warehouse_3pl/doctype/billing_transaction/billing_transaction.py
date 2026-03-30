import frappe
from frappe.model.document import Document


class BillingTransaction(Document):
    def validate(self):
        self.calculate_amount()
        self.set_billing_period()

    def calculate_amount(self):
        if self.rate and self.qty:
            self.amount = self.rate * self.qty

    def set_billing_period(self):
        if self.transaction_date and not self.billing_period:
            self.billing_period = str(self.transaction_date)[:7]
