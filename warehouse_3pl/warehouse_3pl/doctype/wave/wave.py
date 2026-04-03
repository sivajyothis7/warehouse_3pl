import frappe
from frappe.model.document import Document


class Wave(Document):
    def validate(self):
        self.validate_orders()
        self.set_totals()

    def validate_orders(self):
        if not self.orders:
            frappe.throw("At least one order is required in the wave")
        for row in self.orders:
            if row.client_order:
                order = frappe.db.get_value(
                    "Client Order", row.client_order,
                    ["client", "priority", "docstatus"], as_dict=True,
                )
                if not order:
                    frappe.throw(f"Row {row.idx}: Client Order {row.client_order} not found")
                if order.docstatus != 1:
                    frappe.throw(f"Row {row.idx}: Client Order {row.client_order} is not submitted")
                row.client = order.client
                row.priority = order.priority

    def set_totals(self):
        self.total_orders = len(self.orders)

    def release(self):
        if self.status != "Planning":
            frappe.throw("Only waves in Planning status can be released")
        for row in self.orders:
            self._create_pick_task(row)
            frappe.db.set_value("Client Order", row.client_order, "status", "Picking")
        self.db_set("status", "Released")

    def _create_pick_task(self, wave_order_row):
        order = frappe.get_doc("Client Order", wave_order_row.client_order)
        pick_task = frappe.get_doc({
            "doctype": "Pick Task",
            "wave": self.name,
            "client_order": order.name,
            "client": order.client,
            "picking_strategy": self.picking_strategy,
            "status": "Pending",
            "items": [],
        })
        from warehouse_3pl.warehouse_3pl.utils.allocation_engine import allocate_stock

        temp_zone = frappe.db.get_value("Customer", order.client, "default_temp_zone")
        for line in order.items:
            allocations = allocate_stock(
                client=order.client,
                item_code=line.item_code,
                qty=line.qty,
                temperature_zone=temp_zone,
                lot_preference=line.lot_preference,
            )
            for alloc in allocations:
                pick_task.append("items", {
                    "item_code": line.item_code,
                    "qty": alloc["qty"],
                    "from_location": alloc["warehouse"],
                    "lot_no": alloc.get("batch_no") or "",
                    "status": "Pending",
                })
        if pick_task.items:
            pick_task.insert(ignore_permissions=True)


@frappe.whitelist()
def release_wave(wave_name):
    wave = frappe.get_doc("Wave", wave_name)
    wave.release()
    frappe.db.commit()
