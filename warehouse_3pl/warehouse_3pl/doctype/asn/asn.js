frappe.ui.form.on('ASN', {
    setup(frm) {
        frm.set_query('client', function() {
            return { filters: { 'is_3pl_client': 1 } };
        });
    },
    warehouse_job(frm) {
        if (frm.doc.warehouse_job) {
            frappe.db.get_value('Warehouse Job Record', frm.doc.warehouse_job, 'client', function(r) {
                if (r && r.client) {
                    frm.set_value('client', r.client);
                }
            });
        }
    },
    refresh(frm) {
        if (frm.doc.docstatus === 1 && !['Received','Closed','Cancelled'].includes(frm.doc.status)) {
            frm.add_custom_button(__('Create Receiving'), function() {
                frappe.model.open_mapped_doc({
                    method: 'warehouse_3pl.warehouse_3pl.doctype.asn.asn.make_receiving',
                    frm: frm,
                });
            }, __('Actions'));
        }
    }
});
