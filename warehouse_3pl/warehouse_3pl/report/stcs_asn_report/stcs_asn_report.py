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
        {"label": _("Vendor Name"), "fieldname": "vendor_name", "fieldtype": "Data", "width": 180},
        {"label": _("Vendor ASN Number"), "fieldname": "vendor_asn_number", "fieldtype": "Data", "width": 140},
        {"label": _("Pallet Count"), "fieldname": "pallet_count", "fieldtype": "Int", "width": 100},
        {"label": _("Carton Count"), "fieldname": "carton_count", "fieldtype": "Int", "width": 100},
        {"label": _("Estimated Arrival Date"), "fieldname": "eta_date", "fieldtype": "Date", "width": 130},
        {"label": _("Vendor ASN Date"), "fieldname": "vendor_asn_date", "fieldtype": "Date", "width": 130},
        {"label": _("AWB No"), "fieldname": "awb_no", "fieldtype": "Data", "width": 120},
        {"label": _("Version No"), "fieldname": "version_no", "fieldtype": "Data", "width": 100},
        {"label": _("STCS PO No"), "fieldname": "stcs_po_no", "fieldtype": "Data", "width": 140},
        {"label": _("Release No"), "fieldname": "release_no", "fieldtype": "Data", "width": 100},
        {"label": _("Tracking No"), "fieldname": "tracking_no", "fieldtype": "Data", "width": 120},
        {"label": _("STCS PO Line"), "fieldname": "stcs_po_line", "fieldtype": "Data", "width": 100},
        {"label": _("Vendor ASN Line No"), "fieldname": "vendor_asn_line_no", "fieldtype": "Int", "width": 120},
        {"label": _("Supplier Item Code"), "fieldname": "supplier_item_code", "fieldtype": "Data", "width": 160},
        {"label": _("Item Description"), "fieldname": "item_description", "fieldtype": "Data", "width": 250},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 100},
        {"label": _("Shipset"), "fieldname": "shipset", "fieldtype": "Data", "width": 120},
        {"label": _("Status Message"), "fieldname": "status_message", "fieldtype": "Data", "width": 140},
        {"label": _("GRN Number"), "fieldname": "grn_number", "fieldtype": "Link", "options": "Receiving", "width": 160},
    ]


def get_data(filters):
    conditions = []
    params = {}

    if filters.get("from_date"):
        conditions.append("asn.expected_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("asn.expected_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    if filters.get("client"):
        conditions.append("asn.client = %(client)s")
        params["client"] = filters["client"]
    if filters.get("status"):
        conditions.append("asn.status = %(status)s")
        params["status"] = filters["status"]

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT
            asn.client AS vendor_name,
            asn.name AS vendor_asn_number,
            0 AS pallet_count,
            0 AS carton_count,
            asn.expected_date AS eta_date,
            asn.creation AS vendor_asn_date,
            asn.supplier_ref AS awb_no,
            asn.amended_from AS version_no,
            '' AS stcs_po_no,
            '' AS release_no,
            '' AS tracking_no,
            '' AS stcs_po_line,
            line.idx AS vendor_asn_line_no,
            line.item_code AS supplier_item_code,
            item.item_name AS item_description,
            line.expected_qty AS quantity,
            line.lot_no AS shipset,
            asn.status AS status_message,
            rcv.name AS grn_number
        FROM `tabASN` asn
        INNER JOIN `tabASN Line` line ON line.parent = asn.name
        LEFT JOIN `tabItem` item ON item.item_code = line.item_code
        LEFT JOIN `tabReceiving` rcv ON rcv.asn = asn.name AND rcv.docstatus = 1
        {where_clause}
        ORDER BY asn.expected_date DESC, asn.name, line.idx
    """

    return frappe.db.sql(query, params, as_dict=True)
