frappe.ui.form.on('Pack Task', {
    refresh(frm) {
        if (frm.doc.status === 'Pending' && !frm.is_new()) {
            frm.add_custom_button(__('Complete Packing'), function() {
                frappe.call({
                    method: 'warehouse_3pl.warehouse_3pl.doctype.pack_task.pack_task.complete_pack',
                    args: { pack_name: frm.doc.name },
                    callback: function() {
                        frm.reload_doc();
                        frappe.show_alert({message: __('Packing complete! Delivery Note created.'), indicator: 'green'});
                    }
                });
            }).addClass('btn-primary');
        }
        if (frm.doc.delivery_note) {
            frm.add_custom_button(__('Delivery Note'), function() {
                frappe.set_route('Form', 'Delivery Note', frm.doc.delivery_note);
            }, __('View'));
        }
        if (frm.doc.pick_task) {
            frm.add_custom_button(__('Pick Task'), function() {
                frappe.set_route('Form', 'Pick Task', frm.doc.pick_task);
            }, __('View'));
        }
        if (frm.doc.client_order) {
            frm.add_custom_button(__('Client Order'), function() {
                frappe.set_route('Form', 'Client Order', frm.doc.client_order);
            }, __('View'));
        }
    }
});
