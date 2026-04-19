# Copyright (c) 2026, Warehouse 3PL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, nowdate, date_diff


def execute(filters=None):
    filters = filters or {}
    as_of_date = filters.get("as_of_date") or nowdate()

    columns = get_columns()
    data = get_data(filters, as_of_date)
    return columns, data


def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": _("Item Description"), "fieldname": "item_description", "fieldtype": "Data", "width": 260},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 200},
        {"label": _("Owning Client"), "fieldname": "owning_client", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Lot / Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 130},
        {"label": _("Receipt Date"), "fieldname": "receipt_date", "fieldtype": "Date", "width": 120},
        {"label": _("Age (Days)"), "fieldname": "age_days", "fieldtype": "Int", "width": 90},
        {"label": _("0-30 Days"), "fieldname": "bucket_0_30", "fieldtype": "Float", "width": 100},
        {"label": _("31-60 Days"), "fieldname": "bucket_31_60", "fieldtype": "Float", "width": 100},
        {"label": _("61-90 Days"), "fieldname": "bucket_61_90", "fieldtype": "Float", "width": 100},
        {"label": _("91-180 Days"), "fieldname": "bucket_91_180", "fieldtype": "Float", "width": 110},
        {"label": _("181-365 Days"), "fieldname": "bucket_181_365", "fieldtype": "Float", "width": 110},
        {"label": _("Over 365 Days"), "fieldname": "bucket_over_365", "fieldtype": "Float", "width": 110},
        {"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 120},
        {"label": _("Stock Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters, as_of_date):
    conditions = ["sle.posting_date <= %(as_of_date)s", "sle.is_cancelled = 0"]
    params = {"as_of_date": as_of_date}

    if filters.get("warehouse"):
        conditions.append("sle.warehouse = %(warehouse)s")
        params["warehouse"] = filters["warehouse"]
    if filters.get("item_code"):
        conditions.append("sle.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        params["item_group"] = filters["item_group"]
    if filters.get("owning_client"):
        conditions.append("wh.custom_owning_client = %(owning_client)s")
        params["owning_client"] = filters["owning_client"]

    where_clause = "WHERE " + " AND ".join(conditions)

    wh_columns_check = frappe.db.get_table_columns("Warehouse") or []
    owning_client_col = "wh.custom_owning_client" if "custom_owning_client" in wh_columns_check else "''"

    # Aggregate remaining qty & earliest receipt date per (item, warehouse, batch)
    query = f"""
        SELECT
            sle.item_code AS item_code,
            item.item_name AS item_description,
            item.item_group AS item_group,
            item.stock_uom AS uom,
            sle.warehouse AS warehouse,
            {owning_client_col} AS owning_client,
            COALESCE(sle.batch_no, '') AS batch_no,
            MIN(CASE WHEN sle.actual_qty > 0 THEN sle.posting_date ELSE NULL END) AS receipt_date,
            SUM(sle.actual_qty) AS total_qty,
            MAX(sle.valuation_rate) AS valuation_rate
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item ON item.item_code = sle.item_code
        LEFT JOIN `tabWarehouse` wh ON wh.name = sle.warehouse
        {where_clause}
        GROUP BY sle.item_code, sle.warehouse, sle.batch_no
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY sle.warehouse, sle.item_code, sle.batch_no
    """

    rows = frappe.db.sql(query, params, as_dict=True)
    as_of = getdate(as_of_date)

    for row in rows:
        receipt = row.get("receipt_date")
        age = date_diff(as_of, receipt) if receipt else 0
        row["age_days"] = age
        qty = row.get("total_qty") or 0
        row["bucket_0_30"] = qty if 0 <= age <= 30 else 0
        row["bucket_31_60"] = qty if 31 <= age <= 60 else 0
        row["bucket_61_90"] = qty if 61 <= age <= 90 else 0
        row["bucket_91_180"] = qty if 91 <= age <= 180 else 0
        row["bucket_181_365"] = qty if 181 <= age <= 365 else 0
        row["bucket_over_365"] = qty if age > 365 else 0
        row["stock_value"] = qty * (row.get("valuation_rate") or 0)

    return rows
