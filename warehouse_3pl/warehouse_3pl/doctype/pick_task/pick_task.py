import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class PickTask(Document):
    def validate(self):
        if not self.items:
            frappe.throw("At least one pick line is required")

    def start(self):
        if self.status != "Pending":
            frappe.throw("Can only start a Pending pick task")
        self.db_set("status", "In Progress")
        self.db_set("started_at", now_datetime())

    def complete(self):
        if self.status == "Complete":
            frappe.throw("Pick Task is already complete")
        for row in self.items:
            if row.status == "Pending":
                frappe.db.set_value(
                    "Pick Task Line", row.name,
                    {"picked_qty": row.qty, "status": "Picked"},
                )
        self._create_pack_task()
        self._log_billing()
        self.db_set("status", "Complete")
        self.db_set("completed_at", now_datetime())
        if self.client_order:
            frappe.db.set_value("Client Order", self.client_order, "status", "Packing")

    def _create_pack_task(self):
        self.reload()
        pack_task = frappe.get_doc({
            "doctype": "Pack Task",
            "pick_task": self.name,
            "client_order": self.client_order,
            "client": self.client,
            "status": "Pending",
            "items": [],
        })
        for row in self.items:
            picked = row.picked_qty or row.qty
            if picked > 0:
                pack_task.append("items", {"item_code": row.item_code, "qty": picked})
        if pack_task.items:
            pack_task.insert(ignore_permissions=True)

    def _log_billing(self):
        from warehouse_3pl.warehouse_3pl.utils.billing import create_billing_transaction

        total_picked = sum((row.picked_qty or row.qty) for row in self.items)
        if total_picked > 0:
            create_billing_transaction(
                client=self.client,
                activity_type="Picking",
                qty=total_picked,
                source_doctype="Pick Task",
                source_name=self.name,
                uom="Per Unit",
            )


@frappe.whitelist()
def start_pick(pick_name):
    doc = frappe.get_doc("Pick Task", pick_name)
    doc.start()
    frappe.db.commit()

@frappe.whitelist()
def complete_pick(pick_name):
    doc = frappe.get_doc("Pick Task", pick_name)
    doc.complete()
    frappe.db.commit()
