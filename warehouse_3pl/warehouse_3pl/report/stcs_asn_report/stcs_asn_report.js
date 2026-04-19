// Copyright (c) 2026, Warehouse 3PL and contributors
// For license information, please see license.txt

frappe.query_reports["STCS ASN Report"] = {
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
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: "\nDraft\nConfirmed\nReceiving\nReceived\nClosed\nCancelled",
        },
    ],
};
