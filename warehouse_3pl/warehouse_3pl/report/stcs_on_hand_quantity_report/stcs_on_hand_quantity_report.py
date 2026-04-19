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
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": _("Item Description"), "fieldname": "item_description", "fieldtype": "Data", "width": 280},
        {"label": _("Supplier Item Code"), "fieldname": "supplier_item_code", "fieldtype": "Data", "width": 160},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
        {"label": _("Zone / Temp"), "fieldname": "temperature_zone", "fieldtype": "Data", "width": 110},
        {"label": _("Owning Client"), "fieldname": "owning_client", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Actual Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Reserved Qty"), "fieldname": "reserved_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Ordered Qty"), "fieldname": "ordered_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Projected Qty"), "fieldname": "projected_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Available Qty"), "fieldname": "available_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 120},
        {"label": _("Stock Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    conditions = ["bin.actual_qty != 0 OR bin.reserved_qty != 0 OR bin.ordered_qty != 0"]
    params = {}

    if filters.get("warehouse"):
        conditions.append("bin.warehouse = %(warehouse)s")
        params["warehouse"] = filters["warehouse"]
    if filters.get("item_code"):
        conditions.append("bin.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        params["item_group"] = filters["item_group"]
    if filters.get("owning_client"):
        conditions.append("wh.custom_owning_client = %(owning_client)s")
        params["owning_client"] = filters["owning_client"]

    where_clause = "WHERE " + " AND ".join(f"({c})" for c in conditions)

    wh_columns_check = frappe.db.get_table_columns("Warehouse") or []
    owning_client_col = "wh.custom_owning_client" if "custom_owning_client" in wh_columns_check else "''"
    temp_zone_col = "wh.custom_temperature_zone" if "custom_temperature_zone" in wh_columns_check else "''"

    item_columns_check = frappe.db.get_table_columns("Item") or []
    supplier_item_col = "item.custom_supplier_item_code" if "custom_supplier_item_code" in item_columns_check else "''"

    query = f"""
        SELECT
            bin.item_code AS item_code,
            item.item_name AS item_description,
            {supplier_item_col} AS supplier_item_code,
            item.item_group AS item_group,
            item.stock_uom AS uom,
            bin.warehouse AS warehouse,
            {temp_zone_col} AS temperature_zone,
            {owning_client_col} AS owning_client,
            bin.actual_qty AS actual_qty,
            bin.reserved_qty AS reserved_qty,
            bin.ordered_qty AS ordered_qty,
            bin.projected_qty AS projected_qty,
            (bin.actual_qty - bin.reserved_qty) AS available_qty,
            bin.valuation_rate AS valuation_rate,
            bin.stock_value AS stock_value
        FROM `tabBin` bin
        INNER JOIN `tabItem` item ON item.item_code = bin.item_code
        LEFT JOIN `tabWarehouse` wh ON wh.name = bin.warehouse
        {where_clause}
        ORDER BY bin.warehouse, bin.item_code
    """

    return frappe.db.sql(query, params, as_dict=True)
