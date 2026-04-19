// Copyright (c) 2026, Warehouse 3PL and contributors
// For license information, please see license.txt

frappe.query_reports["STCS Stock Aging Report"] = {
    filters: [
        {
            fieldname: "as_of_date",
            label: __("As Of Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            options: "Warehouse",
        },
        {
            fieldname: "item_code",
            label: __("Item Code"),
            fieldtype: "Link",
            options: "Item",
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
        },
        {
            fieldname: "owning_client",
            label: __("Owning Client"),
            fieldtype: "Link",
            options: "Customer",
        },
    ],
};
