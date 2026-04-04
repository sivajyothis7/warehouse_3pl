import frappe
from warehouse_3pl.warehouse_3pl.doctype.rate_card.rate_card import get_rate


def create_billing_transaction(client, activity_type, qty, source_doctype, source_name,
                                item_code=None, uom="Per Unit", transaction_date=None,
                                warehouse_job=None):
    rate, _minimum = get_rate(client, activity_type, uom)
    if not rate and not _minimum:
        return None
    if not transaction_date:
        transaction_date = frappe.utils.today()
    bt = frappe.get_doc({
        "doctype": "Billing Transaction",
        "client": client,
        "activity_type": activity_type,
        "item_code": item_code,
        "qty": qty,
        "uom": uom,
        "rate": rate,
        "source_doctype": source_doctype,
        "source_name": source_name,
        "transaction_date": transaction_date,
        "warehouse_job": warehouse_job or "",
    })
    bt.insert(ignore_permissions=True)
    return bt.name
