# Copyright (c) 2026, Warehouse 3PL and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data


def get_columns():
    return [
        {"label": _("Move Order No"), "fieldname": "move_order_no", "fieldtype": "Link", "options": "Stock Entry", "width": 170},
        {"label": _("Move Order Date"), "fieldname": "move_date", "fieldtype": "Datetime", "width": 140},
        {"label": _("Move Type"), "fieldname": "move_type", "fieldtype": "Data", "width": 140},
        {"label": _("Source"), "fieldname": "source_doctype", "fieldtype": "Data", "width": 150},
        {"label": _("Source Reference"), "fieldname": "source_ref", "fieldtype": "Data", "width": 170},
        {"label": _("Client"), "fieldname": "client", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Warehouse Job"), "fieldname": "warehouse_job", "fieldtype": "Link", "options": "Warehouse Job Record", "width": 160},
        {"label": _("Line No"), "fieldname": "line_no", "fieldtype": "Int", "width": 70},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": _("Item Description"), "fieldname": "item_description", "fieldtype": "Data", "width": 250},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 90},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": _("From Warehouse"), "fieldname": "from_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"label": _("To Warehouse"), "fieldname": "to_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"label": _("Lot / Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 120},
        {"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 140},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Operator"), "fieldname": "operator", "fieldtype": "Link", "options": "User", "width": 150},
    ]


def get_data(filters):
    conditions = []
    params = {}

    if filters.get("from_date"):
        conditions.append("se.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("se.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    if filters.get("client"):
        conditions.append("se.custom_client = %(client)s")
        params["client"] = filters["client"]
    if filters.get("warehouse_job"):
        conditions.append("se.custom_warehouse_job = %(warehouse_job)s")
        params["warehouse_job"] = filters["warehouse_job"]
    if filters.get("move_type"):
        conditions.append("se.stock_entry_type = %(move_type)s")
        params["move_type"] = filters["move_type"]

    conditions.append("se.docstatus = 1")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    se_columns_check = frappe.db.get_table_columns("Stock Entry") or []
    client_col = "se.custom_client" if "custom_client" in se_columns_check else ("se.client" if "client" in se_columns_check else "''")
    job_col = "se.custom_warehouse_job" if "custom_warehouse_job" in se_columns_check else "''"
    operator_col = "se.custom_operator" if "custom_operator" in se_columns_check else "se.owner"

    query = f"""
        SELECT
            se.name AS move_order_no,
            CONCAT(se.posting_date, ' ', se.posting_time) AS move_date,
            se.stock_entry_type AS move_type,
            se.doctype AS source_doctype,
            COALESCE(se.work_order, se.pro_doc_name, se.name) AS source_ref,
            {client_col} AS client,
            {job_col} AS warehouse_job,
            sed.idx AS line_no,
            sed.item_code AS item_code,
            COALESCE(sed.item_name, item.item_name) AS item_description,
            sed.qty AS qty,
            sed.uom AS uom,
            sed.s_warehouse AS from_warehouse,
            sed.t_warehouse AS to_warehouse,
            sed.batch_no AS batch_no,
            sed.serial_no AS serial_no,
            CASE WHEN se.docstatus = 1 THEN 'Completed' WHEN se.docstatus = 0 THEN 'Draft' ELSE 'Cancelled' END AS status,
            {operator_col} AS operator
        FROM `tabStock Entry` se
        INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
        LEFT JOIN `tabItem` item ON item.item_code = sed.item_code
        {where_clause}
        ORDER BY se.posting_date DESC, se.posting_time DESC, se.name, sed.idx
    """

    return frappe.db.sql(query, params, as_dict=True)
