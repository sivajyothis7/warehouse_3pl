import frappe
from frappe.model.document import Document


class ClientOrder(Document):
    def validate(self):
        self.validate_client_is_3pl()
        self.validate_items()

    def on_submit(self):
        self.db_set("status", "Confirmed")
        self.allocate_inventory()

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
            if row.qty <= 0:
                frappe.throw(f"Row {row.idx}: Qty must be greater than 0")

    def allocate_inventory(self):
        from warehouse_3pl.warehouse_3pl.utils.allocation_engine import allocate_stock
        temp_zone = frappe.db.get_value("Customer", self.client, "default_temp_zone")
        for row in self.items:
            allocations = allocate_stock(
                client=self.client,
                item_code=row.item_code,
                qty=row.qty,
                temperature_zone=temp_zone,
                lot_preference=row.lot_preference,
            )
            allocated = sum(a["qty"] for a in allocations)
            frappe.db.set_value("Client Order Line", row.name, "allocated_qty", allocated)
        self.reload()
        fully_allocated = all(row.allocated_qty >= row.qty for row in self.items)
        if fully_allocated:
            self.db_set("status", "Allocated")
        else:
            self.db_set("status", "Confirmed")
            frappe.msgprint("Some items could not be fully allocated", indicator="orange", alert=True)
