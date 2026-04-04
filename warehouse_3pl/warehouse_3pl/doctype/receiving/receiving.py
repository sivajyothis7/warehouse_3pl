import frappe
from frappe.model.document import Document
from frappe.utils import today


class Receiving(Document):
    def validate(self):
        self.validate_client_is_3pl()
        self.validate_items()
        self.pull_from_asn()

    def on_submit(self):
        self.create_stock_entry()
        self.create_putaway_tasks()
        self.log_billing_transaction()
        self.update_asn_status()
        self.db_set("status", "Complete")

    def on_cancel(self):
        self.cancel_stock_entry()
        self.cancel_putaway_tasks()
        self.db_set("status", "Cancelled")

    def validate_client_is_3pl(self):
        is_3pl = frappe.db.get_value("Customer", self.client, "is_3pl_client")
        if not is_3pl:
            frappe.throw(f"Customer {self.client} is not a 3PL client")

    def validate_items(self):
        if not self.items:
            frappe.throw("At least one item line is required")
        for row in self.items:
            if row.received_qty < 0:
                frappe.throw(f"Row {row.idx}: Received Qty cannot be negative")

    def pull_from_asn(self):
        if self.asn and not self.client:
            self.client = frappe.db.get_value("ASN", self.asn, "client")

    def create_stock_entry(self):
        company = None
        if self.warehouse_job:
            company = frappe.db.get_value("Warehouse Job Record", self.warehouse_job, "company")
        if not company:
            company = frappe.db.get_value("Warehouse", self.staging_location, "company")
        if not company:
            company = frappe.db.get_single_value("Global Defaults", "default_company")

        cost_center = frappe.db.get_value("Company", company, "cost_center")

        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "posting_date": self.receiving_date or today(),
            "company": company,
            "client": self.client,
            "custom_warehouse_job": self.warehouse_job or "",
            "asn_reference": self.asn or "",
            "reason_code": "Receiving",
            "items": [],
        })

        for row in self.items:
            if row.received_qty <= 0:
                continue
            se_item = {
                "item_code": row.item_code,
                "qty": row.received_qty,
                "t_warehouse": self.staging_location,
                "basic_rate": 0,
                "allow_zero_valuation_rate": 1,
                "cost_center": cost_center,
            }
            se.append("items", se_item)

        if not se.items:
            return

        se.insert(ignore_permissions=True)
        se.submit()
        self.db_set("stock_entry", se.name)

    def create_putaway_tasks(self):
        from warehouse_3pl.warehouse_3pl.utils.putaway_engine import suggest_putaway_location

        for row in self.items:
            if row.received_qty <= 0:
                continue
            temp_zone = frappe.db.get_value("Item", row.item_code, "storage_temp_zone")
            if not temp_zone:
                temp_zone = frappe.db.get_value("Customer", self.client, "default_temp_zone")

            target = suggest_putaway_location(
                client=self.client,
                item_code=row.item_code,
                qty=row.received_qty,
                temperature_zone=temp_zone,
            )

            frappe.get_doc({
                "doctype": "Putaway Task",
                "receiving_ref": self.name,
                "client": self.client,
                "item_code": row.item_code,
                "qty": row.received_qty,
                "lot_no": row.lot_no,
                "source_location": self.staging_location,
                "target_location": target or self.staging_location,
                "status": "Pending",
            }).insert(ignore_permissions=True)

    def log_billing_transaction(self):
        from warehouse_3pl.warehouse_3pl.utils.billing import create_billing_transaction

        total_qty = sum(row.received_qty for row in self.items if row.received_qty > 0)
        if total_qty <= 0:
            return
        bt_name = create_billing_transaction(
            client=self.client,
            activity_type="Receiving",
            qty=total_qty,
            source_doctype="Receiving",
            source_name=self.name,
            uom="Per Unit",
            transaction_date=self.receiving_date,
            warehouse_job=self.warehouse_job,
        )
        if bt_name:
            self.db_set("billing_transaction", bt_name)

    def update_asn_status(self):
        if self.asn:
            frappe.db.set_value("ASN", self.asn, "status", "Received")

    def cancel_stock_entry(self):
        if self.stock_entry:
            se = frappe.get_doc("Stock Entry", self.stock_entry)
            if se.docstatus == 1:
                se.cancel()

    def cancel_putaway_tasks(self):
        tasks = frappe.get_all("Putaway Task", filters={"receiving_ref": self.name}, pluck="name")
        for task_name in tasks:
            task = frappe.get_doc("Putaway Task", task_name)
            if task.status != "Complete":
                task.db_set("status", "Cancelled")
