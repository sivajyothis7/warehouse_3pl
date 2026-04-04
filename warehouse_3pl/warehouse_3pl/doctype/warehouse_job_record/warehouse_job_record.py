import frappe
from frappe.model.document import Document


class WarehouseJobRecord(Document):
    def validate(self):
        self.set_default_company()
        self.validate_client_is_3pl()
        self.calculate_stock_summary()
        self.calculate_pnl()

    def set_default_company(self):
        if not self.company:
            self.company = frappe.db.get_single_value("Global Defaults", "default_company")

    def validate_client_is_3pl(self):
        if self.client:
            is_3pl = frappe.db.get_value("Customer", self.client, "is_3pl_client")
            if not is_3pl:
                frappe.throw(f"Customer {self.client} is not a 3PL client")

    def calculate_stock_summary(self):
        total_in = sum(row.qty_in or 0 for row in self.stock_movements)
        total_out = sum(row.qty_out or 0 for row in self.stock_movements)
        self.total_in_qty = total_in
        self.total_out_qty = total_out
        self.balance_qty = total_in - total_out

    def calculate_pnl(self):
        revenue = sum(row.amount or 0 for row in self.vouchers if row.voucher_type in ["Sales Invoice", "Billing Transaction"])
        cost = sum(row.amount or 0 for row in self.vouchers if row.voucher_type in ["Purchase Invoice", "Journal Entry"])
        self.total_revenue = revenue
        self.total_cost = cost
        self.gross_profit = revenue - cost

    @frappe.whitelist()
    def fetch_linked_vouchers(self):
        """Fetch all vouchers linked to this job."""
        self.vouchers = []

        # Billing Transactions
        bts = frappe.get_all("Billing Transaction",
            filters={"warehouse_job": self.name},
            fields=["name", "transaction_date", "amount", "client", "activity_type"])
        for bt in bts:
            self.append("vouchers", {
                "voucher_type": "Billing Transaction",
                "voucher_no": bt.name,
                "voucher_date": bt.transaction_date,
                "amount": bt.amount or 0,
                "party": bt.client,
                "party_type": "Customer",
            })

        # Sales Invoices
        sis = frappe.get_all("Sales Invoice",
            filters={"custom_warehouse_job": self.name, "docstatus": 1},
            fields=["name", "posting_date", "grand_total", "customer"])
        for si in sis:
            self.append("vouchers", {
                "voucher_type": "Sales Invoice",
                "voucher_no": si.name,
                "voucher_date": si.posting_date,
                "amount": si.grand_total or 0,
                "party": si.customer,
                "party_type": "Customer",
            })

        # Purchase Invoices
        pis = frappe.get_all("Purchase Invoice",
            filters={"custom_warehouse_job": self.name, "docstatus": 1},
            fields=["name", "posting_date", "grand_total", "supplier"])
        for pi in pis:
            self.append("vouchers", {
                "voucher_type": "Purchase Invoice",
                "voucher_no": pi.name,
                "voucher_date": pi.posting_date,
                "amount": pi.grand_total or 0,
                "party": pi.supplier,
                "party_type": "Supplier",
            })

        # Journal Entries (expenses against job)
        jes = frappe.get_all("Journal Entry",
            filters={"custom_warehouse_job": self.name, "docstatus": 1},
            fields=["name", "posting_date", "total_debit", "remark"])
        for je in jes:
            self.append("vouchers", {
                "voucher_type": "Journal Entry",
                "voucher_no": je.name,
                "voucher_date": je.posting_date,
                "amount": je.total_debit or 0,
                "party": je.remark or "",
            })

        self.calculate_pnl()
        self.save()
        return {"status": "ok", "count": len(self.vouchers)}

    @frappe.whitelist()
    def fetch_stock_movements(self):
        """Fetch stock movements from linked receivings and delivery notes."""
        self.stock_movements = []

        # From Receivings
        receivings = frappe.get_all("Receiving",
            filters={"warehouse_job": self.name, "docstatus": 1},
            pluck="name")
        for rcv_name in receivings:
            lines = frappe.get_all("Receiving Line",
                filters={"parent": rcv_name},
                fields=["item_code", "received_qty", "lot_no"])
            rcv = frappe.get_doc("Receiving", rcv_name)
            for line in lines:
                self.append("stock_movements", {
                    "item_code": line.item_code,
                    "qty_in": line.received_qty,
                    "qty_out": 0,
                    "warehouse": rcv.staging_location,
                    "batch_no": line.lot_no,
                    "movement_date": rcv.receiving_date,
                    "source_doctype": "Receiving",
                    "source_name": rcv_name,
                })

        # From Delivery Notes
        dns = frappe.get_all("Delivery Note",
            filters={"custom_warehouse_job": self.name, "docstatus": 1},
            pluck="name")
        for dn_name in dns:
            dn = frappe.get_doc("Delivery Note", dn_name)
            for item in dn.items:
                self.append("stock_movements", {
                    "item_code": item.item_code,
                    "qty_in": 0,
                    "qty_out": item.qty,
                    "warehouse": item.warehouse,
                    "movement_date": dn.posting_date,
                    "source_doctype": "Delivery Note",
                    "source_name": dn_name,
                })

        self.calculate_stock_summary()
        self.save()
        return {"status": "ok", "movements": len(self.stock_movements)}


@frappe.whitelist()
def make_delivery_note(job_name):
    """Create a Delivery Note pre-filled with items from this job's receivings."""
    job = frappe.get_doc("Warehouse Job Record", job_name)

    dn = frappe.new_doc("Delivery Note")
    dn.customer = job.client
    dn.company = job.company
    dn.custom_warehouse_job = job.name
    dn.client = job.client

    # Get items from receivings linked to this job
    receivings = frappe.get_all("Receiving",
        filters={"warehouse_job": job_name},
        pluck="name")

    items_map = {}
    for rcv_name in receivings:
        lines = frappe.get_all("Receiving Line",
            filters={"parent": rcv_name},
            fields=["item_code", "received_qty"])
        rcv = frappe.get_doc("Receiving", rcv_name)
        for line in lines:
            key = line.item_code
            if key not in items_map:
                items_map[key] = {
                    "item_code": line.item_code,
                    "qty": 0,
                    "warehouse": rcv.staging_location,
                }
            items_map[key]["qty"] += line.received_qty or 0

    for item_data in items_map.values():
        if item_data["qty"] > 0:
            dn.append("items", item_data)

    return dn


@frappe.whitelist()
def make_sales_invoice(job_name):
    """Create a Sales Invoice from billing transactions linked to this job."""
    job = frappe.get_doc("Warehouse Job Record", job_name)

    si = frappe.new_doc("Sales Invoice")
    si.customer = job.client
    si.company = job.company
    si.custom_warehouse_job = job.name

    # Get billing transactions for this job
    bts = frappe.get_all("Billing Transaction",
        filters={"warehouse_job": job_name},
        fields=["name", "activity_type", "qty", "rate", "amount", "uom"])

    for bt in bts:
        si.append("items", {
            "item_name": bt.activity_type,
            "description": f"{bt.activity_type} - {bt.qty} {bt.uom}",
            "qty": bt.qty or 1,
            "rate": bt.rate or 0,
            "uom": "Nos",
        })

    if not si.items:
        frappe.msgprint("No billing transactions found for this job. You can add items manually.")

    return si


@frappe.whitelist()
def get_job_dashboard_data(job_name):
    """API for the overview dashboard. Calculates live stock from linked docs."""
    job = frappe.get_doc("Warehouse Job Record", job_name)

    asn_count = frappe.db.count("ASN", {"warehouse_job": job_name})
    rcv_count = frappe.db.count("Receiving", {"warehouse_job": job_name})
    order_count = frappe.db.count("Client Order", {"warehouse_job": job_name})
    billing_count = frappe.db.count("Billing Transaction", {"warehouse_job": job_name})
    billing_total = frappe.db.get_value("Billing Transaction",
        {"warehouse_job": job_name}, "sum(amount)") or 0
    dn_count = frappe.db.count("Delivery Note", {"custom_warehouse_job": job_name})

    # Calculate live stock in from submitted receivings
    total_in = 0
    receivings = frappe.get_all("Receiving",
        filters={"warehouse_job": job_name, "docstatus": 1},
        pluck="name")
    for rcv_name in receivings:
        qty = frappe.db.sql(
            "SELECT SUM(received_qty) FROM `tabReceiving Line` WHERE parent=%s",
            rcv_name
        )
        total_in += (qty[0][0] or 0) if qty else 0

    # Also count from submitted receivings without docstatus filter (Draft receivings)
    if not total_in:
        receivings_all = frappe.get_all("Receiving",
            filters={"warehouse_job": job_name},
            pluck="name")
        for rcv_name in receivings_all:
            qty = frappe.db.sql(
                "SELECT SUM(received_qty) FROM `tabReceiving Line` WHERE parent=%s",
                rcv_name
            )
            total_in += (qty[0][0] or 0) if qty else 0

    # Calculate live stock out from submitted delivery notes
    total_out = 0
    dns = frappe.get_all("Delivery Note",
        filters={"custom_warehouse_job": job_name, "docstatus": 1},
        pluck="name")
    for dn_name in dns:
        qty = frappe.db.sql(
            "SELECT SUM(qty) FROM `tabDelivery Note Item` WHERE parent=%s",
            dn_name
        )
        total_out += (qty[0][0] or 0) if qty else 0

    balance = total_in - total_out

    return {
        "client": job.client,
        "client_name": job.client_name,
        "job_status": job.job_status,
        "date": str(job.date),
        "total_in_qty": total_in,
        "total_out_qty": total_out,
        "balance_qty": balance,
        "total_revenue": job.total_revenue or 0,
        "total_cost": job.total_cost or 0,
        "gross_profit": job.gross_profit or 0,
        "counts": {
            "asn": asn_count,
            "receiving": rcv_count,
            "client_order": order_count,
            "billing": billing_count,
            "billing_total": billing_total,
            "delivery_note": dn_count,
        }
    }
