// Copyright (c) 2026, Warehouse 3PL and contributors
// For license information, please see license.txt

frappe.query_reports["STCS GRN Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "client",
            label: __("Client"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "warehouse_job",
            label: __("Warehouse Job"),
            fieldtype: "Link",
            options: "Warehouse Job Record",
        },
        {
            fieldname: "docstatus",
            label: __("Document Status"),
            fieldtype: "Select",
            options: "\n0\n1\n2",
            default: "1",
        },
    ],
};
