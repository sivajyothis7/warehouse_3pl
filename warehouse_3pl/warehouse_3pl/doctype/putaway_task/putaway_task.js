frappe.ui.form.on('Putaway Task', {
    refresh(frm) {
        if (frm.doc.status === 'Pending' && !frm.is_new()) {
            frm.add_custom_button(__('Complete Putaway'), function() {
                frappe.call({
                    method: 'warehouse_3pl.warehouse_3pl.doctype.putaway_task.putaway_task.complete_putaway',
                    args: { task_name: frm.doc.name },
                    callback: function() {
                        frm.reload_doc();
                        frappe.show_alert({message: __('Putaway complete! Stock transferred.'), indicator: 'green'});
                    }
                });
            }).addClass('btn-primary');
        }
        if (frm.doc.stock_entry) {
            frm.add_custom_button(__('Stock Entry'), function() {
                frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
            }, __('View'));
        }
        if (frm.doc.receiving_ref) {
            frm.add_custom_button(__('Receiving'), function() {
                frappe.set_route('Form', 'Receiving', frm.doc.receiving_ref);
            }, __('View'));
        }
    }
});
