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
        {"label": _("GRN Number"), "fieldname": "grn_number", "fieldtype": "Link", "options": "Receiving", "width": 160},
        {"label": _("GRN Date"), "fieldname": "grn_date", "fieldtype": "Date", "width": 110},
        {"label": _("Vendor / Client"), "fieldname": "client", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("ASN Number"), "fieldname": "asn_number", "fieldtype": "Link", "options": "ASN", "width": 140},
        {"label": _("Warehouse Job"), "fieldname": "warehouse_job", "fieldtype": "Link", "options": "Warehouse Job Record", "width": 160},
        {"label": _("Received By"), "fieldname": "received_by", "fieldtype": "Link", "options": "User", "width": 150},
        {"label": _("Staging Location"), "fieldname": "staging_location", "fieldtype": "Link", "options": "Warehouse", "width": 170},
        {"label": _("STCS PO No"), "fieldname": "stcs_po_no", "fieldtype": "Data", "width": 140},
        {"label": _("Release No"), "fieldname": "release_no", "fieldtype": "Data", "width": 100},
        {"label": _("Project No"), "fieldname": "project_no", "fieldtype": "Data", "width": 100},
        {"label": _("Shipset No"), "fieldname": "shipset_no", "fieldtype": "Data", "width": 100},
        {"label": _("Truck Driver"), "fieldname": "truck_driver", "fieldtype": "Data", "width": 150},
        {"label": _("Driver ID / Iqama"), "fieldname": "driver_iqama", "fieldtype": "Data", "width": 130},
        {"label": _("Check-in Date"), "fieldname": "check_in_date", "fieldtype": "Datetime", "width": 140},
        {"label": _("Line No"), "fieldname": "line_no", "fieldtype": "Int", "width": 80},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": _("Supplier Item Code"), "fieldname": "supplier_item_code", "fieldtype": "Data", "width": 160},
        {"label": _("Item Description"), "fieldname": "item_description", "fieldtype": "Data", "width": 250},
        {"label": _("Expected Qty"), "fieldname": "expected_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Received Qty"), "fieldname": "received_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Rejected Qty"), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 100},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": _("Lot / Batch No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 120},
        {"label": _("Storage Location"), "fieldname": "storage_location", "fieldtype": "Data", "width": 140},
        {"label": _("Condition"), "fieldname": "condition", "fieldtype": "Data", "width": 100},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]


def get_data(filters):
    conditions = []
    params = {}

    if filters.get("from_date"):
        conditions.append("rcv.receiving_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("rcv.receiving_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    if filters.get("client"):
        conditions.append("rcv.client = %(client)s")
        params["client"] = filters["client"]
    if filters.get("warehouse_job"):
        conditions.append("rcv.warehouse_job = %(warehouse_job)s")
        params["warehouse_job"] = filters["warehouse_job"]
    if filters.get("docstatus"):
        conditions.append("rcv.docstatus = %(docstatus)s")
        params["docstatus"] = filters["docstatus"]
    else:
        conditions.append("rcv.docstatus IN (0, 1)")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # Use dynamic column names for custom fields that may not exist yet
    grn_columns_check = frappe.db.get_table_columns("Receiving") or []
    rcv_line_columns_check = frappe.db.get_table_columns("Receiving Line") or []

    truck_driver_col = "rcv.truck_driver_name" if "truck_driver_name" in grn_columns_check else "'' "
    driver_iqama_col = "rcv.truck_driver_iqama" if "truck_driver_iqama" in grn_columns_check else "'' "
    check_in_col = "rcv.check_in_date" if "check_in_date" in grn_columns_check else "rcv.creation"
    rejected_qty_col = "line.rejected_qty" if "rejected_qty" in rcv_line_columns_check else "0"
    condition_col = "line.`condition`" if "condition" in rcv_line_columns_check else "'Good'"
    storage_loc_col = "line.storage_location" if "storage_location" in rcv_line_columns_check else "rcv.staging_location"

    query = f"""
        SELECT
            rcv.name AS grn_number,
            rcv.receiving_date AS grn_date,
            rcv.client AS client,
            rcv.asn AS asn_number,
            rcv.warehouse_job AS warehouse_job,
            rcv.received_by AS received_by,
            rcv.staging_location AS staging_location,
            '' AS stcs_po_no,
            '' AS release_no,
            '' AS project_no,
            '' AS shipset_no,
            {truck_driver_col} AS truck_driver,
            {driver_iqama_col} AS driver_iqama,
            {check_in_col} AS check_in_date,
            line.idx AS line_no,
            line.item_code AS item_code,
            item.custom_supplier_item_code AS supplier_item_code,
            item.item_name AS item_description,
            COALESCE(line.expected_qty, 0) AS expected_qty,
            COALESCE(line.received_qty, 0) AS received_qty,
            {rejected_qty_col} AS rejected_qty,
            item.stock_uom AS uom,
            line.lot_no AS lot_no,
            {storage_loc_col} AS storage_location,
            {condition_col} AS `condition`,
            rcv.status AS status
        FROM `tabReceiving` rcv
        INNER JOIN `tabReceiving Line` line ON line.parent = rcv.name
        LEFT JOIN `tabItem` item ON item.item_code = line.item_code
        {where_clause}
        ORDER BY rcv.receiving_date DESC, rcv.name, line.idx
    """

    return frappe.db.sql(query, params, as_dict=True)
