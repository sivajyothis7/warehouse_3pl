import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def get_custom_fields():
    """Return dict of {doctype: [field_defs]} for all ERPNext extensions."""
    return {
        "Customer": [
            {
                "fieldname": "tpl_section",
                "fieldtype": "Section Break",
                "label": "3PL Client Settings",
                "insert_after": "language",
                "depends_on": "eval:doc.is_3pl_client",
                "collapsible": 1,
            },
            {
                "fieldname": "is_3pl_client",
                "fieldtype": "Check",
                "label": "Is 3PL Client",
                "insert_after": "customer_type",
                "bold": 1,
                "description": "Check this to enable 3PL warehouse client features",
            },
            {
                "fieldname": "client_code",
                "fieldtype": "Data",
                "label": "Client Code",
                "insert_after": "tpl_section",
                "unique": 1,
                "description": "Defaults to Customer ID if left blank",
                "depends_on": "eval:doc.is_3pl_client",
            },
            {
                "fieldname": "default_temp_zone",
                "fieldtype": "Select",
                "label": "Default Temperature Zone",
                "insert_after": "client_code",
                "options": "\nFrozen\nRefrigerated\nCool\nControlled Ambient\nAmbient",
                "depends_on": "eval:doc.is_3pl_client",
            },
            {
                "fieldname": "tpl_col_break",
                "fieldtype": "Column Break",
                "insert_after": "default_temp_zone",
            },
            {
                "fieldname": "carrier_preferences",
                "fieldtype": "Small Text",
                "label": "Carrier Preferences",
                "insert_after": "tpl_col_break",
                "depends_on": "eval:doc.is_3pl_client",
            },
            {
                "fieldname": "active_rate_card",
                "fieldtype": "Link",
                "label": "Active Rate Card",
                "insert_after": "carrier_preferences",
                "options": "Rate Card",
                "depends_on": "eval:doc.is_3pl_client",
            },
            {
                "fieldname": "client_status",
                "fieldtype": "Select",
                "label": "Client Status",
                "insert_after": "active_rate_card",
                "options": "\nActive\nOnboarding\nSuspended",
                "default": "Onboarding",
                "depends_on": "eval:doc.is_3pl_client",
            },
            {
                "fieldname": "portal_user",
                "fieldtype": "Link",
                "label": "Portal User",
                "insert_after": "client_status",
                "options": "User",
                "depends_on": "eval:doc.is_3pl_client",
            },
        ],
        "Warehouse": [
            {
                "fieldname": "tpl_section",
                "fieldtype": "Section Break",
                "label": "3PL Location Details",
                "insert_after": "disabled",
            },
            {
                "fieldname": "temperature_zone",
                "fieldtype": "Select",
                "label": "Temperature Zone",
                "insert_after": "tpl_section",
                "options": "\nFrozen\nRefrigerated\nCool\nControlled Ambient\nAmbient",
            },
            {
                "fieldname": "zone_type",
                "fieldtype": "Data",
                "label": "Zone Type",
                "insert_after": "temperature_zone",
                "description": "Zone identifier e.g. FRZ-A, AMB-B",
            },
            {
                "fieldname": "location_type",
                "fieldtype": "Select",
                "label": "Location Type",
                "insert_after": "zone_type",
                "options": "\nPick Face\nReserve\nStaging\nDock\nQC Hold\nShipping Dock\nReceiving Dock",
            },
            {
                "fieldname": "tpl_col_break",
                "fieldtype": "Column Break",
                "insert_after": "location_type",
            },
            {
                "fieldname": "aisle",
                "fieldtype": "Data",
                "label": "Aisle",
                "insert_after": "tpl_col_break",
            },
            {
                "fieldname": "rack",
                "fieldtype": "Data",
                "label": "Rack",
                "insert_after": "aisle",
            },
            {
                "fieldname": "level",
                "fieldtype": "Data",
                "label": "Level",
                "insert_after": "rack",
            },
            {
                "fieldname": "bin_code",
                "fieldtype": "Data",
                "label": "Bin Code",
                "insert_after": "level",
            },
            {
                "fieldname": "tpl_capacity_section",
                "fieldtype": "Section Break",
                "label": "Capacity",
                "insert_after": "bin_code",
            },
            {
                "fieldname": "max_weight_kg",
                "fieldtype": "Float",
                "label": "Max Weight (kg)",
                "insert_after": "tpl_capacity_section",
            },
            {
                "fieldname": "max_volume_cbm",
                "fieldtype": "Float",
                "label": "Max Volume (cbm)",
                "insert_after": "max_weight_kg",
            },
            {
                "fieldname": "owning_client",
                "fieldtype": "Link",
                "label": "Owning Client",
                "insert_after": "max_volume_cbm",
                "options": "Customer",
                "description": "If this location is dedicated to a specific 3PL client",
            },
        ],
        "Item": [
            {
                "fieldname": "tpl_section",
                "fieldtype": "Section Break",
                "label": "3PL Settings",
                "insert_after": "is_fixed_asset",
            },
            {
                "fieldname": "storage_temp_zone",
                "fieldtype": "Select",
                "label": "Storage Temperature Zone",
                "insert_after": "tpl_section",
                "options": "\nFrozen\nRefrigerated\nCool\nControlled Ambient\nAmbient",
            },
            {
                "fieldname": "hazmat_class",
                "fieldtype": "Data",
                "label": "Hazmat Class",
                "insert_after": "storage_temp_zone",
                "description": "UN hazmat class if applicable",
            },
            {
                "fieldname": "tpl_col_break",
                "fieldtype": "Column Break",
                "insert_after": "hazmat_class",
            },
            {
                "fieldname": "requires_lot_tracking",
                "fieldtype": "Check",
                "label": "Requires Lot Tracking",
                "insert_after": "tpl_col_break",
            },
            {
                "fieldname": "velocity_class",
                "fieldtype": "Select",
                "label": "Velocity Class",
                "insert_after": "requires_lot_tracking",
                "options": "\nA\nB\nC",
                "description": "A=fast, B=medium, C=slow mover",
            },
        ],
        "Batch": [
            {
                "fieldname": "supplier_lot_no",
                "fieldtype": "Data",
                "label": "Supplier Lot No",
                "insert_after": "batch_id",
            },
            {
                "fieldname": "receiving_date",
                "fieldtype": "Date",
                "label": "Receiving Date",
                "insert_after": "supplier_lot_no",
            },
            {
                "fieldname": "country_of_origin",
                "fieldtype": "Link",
                "label": "Country of Origin",
                "insert_after": "receiving_date",
                "options": "Country",
            },
            {
                "fieldname": "qc_status",
                "fieldtype": "Select",
                "label": "QC Status",
                "insert_after": "country_of_origin",
                "options": "\nPending\nPassed\nFailed\nHold",
                "default": "Pending",
            },
        ],
        "Stock Entry": [
            {
                "fieldname": "client",
                "fieldtype": "Link",
                "label": "3PL Client",
                "insert_after": "stock_entry_type",
                "options": "Customer",
                "description": "3PL client who owns this inventory",
            },
            {
                "fieldname": "custom_warehouse_job",
                "fieldtype": "Link",
                "label": "Warehouse Job",
                "insert_after": "client",
                "options": "Warehouse Job Record",
            },
            {
                "fieldname": "asn_reference",
                "fieldtype": "Data",
                "label": "ASN Reference",
                "insert_after": "custom_warehouse_job",
            },
            {
                "fieldname": "reason_code",
                "fieldtype": "Select",
                "label": "Reason Code",
                "insert_after": "asn_reference",
                "options": "\nReceiving\nPutaway\nPick\nAdjustment\nDamage\nExpiry\nReturn\nTransfer",
            },
            {
                "fieldname": "operator",
                "fieldtype": "Link",
                "label": "Operator",
                "insert_after": "reason_code",
                "options": "User",
            },
        ],
        "Delivery Note": [
            {
                "fieldname": "client",
                "fieldtype": "Link",
                "label": "3PL Client",
                "insert_after": "customer",
                "options": "Customer",
                "description": "3PL client who owns this shipment",
            },
            {
                "fieldname": "custom_warehouse_job",
                "fieldtype": "Link",
                "label": "Warehouse Job",
                "insert_after": "client",
                "options": "Warehouse Job Record",
            },
            {
                "fieldname": "carrier",
                "fieldtype": "Data",
                "label": "Carrier",
                "insert_after": "custom_warehouse_job",
            },
            {
                "fieldname": "tracking_number",
                "fieldtype": "Data",
                "label": "Tracking Number",
                "insert_after": "carrier",
            },
            {
                "fieldname": "wave_reference",
                "fieldtype": "Data",
                "label": "Wave Reference",
                "insert_after": "tracking_number",
            },
            {
                "fieldname": "bol_number",
                "fieldtype": "Data",
                "label": "BOL Number",
                "insert_after": "wave_reference",
                "description": "Bill of Lading number",
            },
        ],
        "Sales Invoice": [
            {
                "fieldname": "custom_warehouse_job",
                "fieldtype": "Link",
                "label": "Warehouse Job",
                "insert_after": "customer",
                "options": "Warehouse Job Record",
            },
        ],
        "Purchase Invoice": [
            {
                "fieldname": "custom_warehouse_job",
                "fieldtype": "Link",
                "label": "Warehouse Job",
                "insert_after": "supplier",
                "options": "Warehouse Job Record",
            },
        ],
    }


def setup_custom_fields():
    """Create all custom fields. Called from hooks.py after_install."""
    create_custom_fields(get_custom_fields(), ignore_validate=True)
    frappe.db.commit()
