frappe.ui.form.on('Receiving', {
    setup(frm) {
        frm.set_query('client', function() {
            return { filters: { 'is_3pl_client': 1 } };
        });
    },
    asn(frm) {
        if (frm.doc.asn) {
            frappe.call({
                method: 'frappe.client.get',
                args: { doctype: 'ASN', name: frm.doc.asn },
                callback: function(r) {
                    if (r.message) {
                        var asn = r.message;
                        frm.set_value('client', asn.client);
                        if (asn.warehouse_job) {
                            frm.set_value('warehouse_job', asn.warehouse_job);
                        }
                        frm.clear_table('items');
                        (asn.items || []).forEach(function(row) {
                            var child = frm.add_child('items');
                            child.item_code = row.item_code;
                            child.expected_qty = row.expected_qty;
                            child.received_qty = row.expected_qty;
                            child.lot_no = row.lot_no || '';
                            child.condition = 'Good';
                        });
                        frm.refresh_fields();
                        frappe.show_alert({message: __('Items fetched from ASN'), indicator: 'green'});
                    }
                }
            });
        }
    },
    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.stock_entry) {
            frm.add_custom_button(__('Stock Entry'), function() {
                frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
            }, __('View'));
        }
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Putaway Tasks'), function() {
                frappe.set_route('List', 'Putaway Task', {receiving_ref: frm.doc.name});
            }, __('View'));
        }
    }
});
