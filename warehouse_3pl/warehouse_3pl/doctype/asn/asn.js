frappe.ui.form.on('ASN', {
    setup(frm) {
        frm.set_query('client', function() {
            return { filters: { 'is_3pl_client': 1 } };
        });
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
