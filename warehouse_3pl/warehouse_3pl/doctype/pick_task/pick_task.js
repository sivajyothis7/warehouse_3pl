frappe.ui.form.on('Pick Task', {
    refresh(frm) {
        if (frm.doc.status === 'Pending' && !frm.is_new()) {
            frm.add_custom_button(__('Start Picking'), function() {
                frappe.call({
                    method: 'warehouse_3pl.warehouse_3pl.doctype.pick_task.pick_task.start_pick',
                    args: { pick_name: frm.doc.name },
                    callback: function() {
                        frm.reload_doc();
                        frappe.show_alert({message: __('Picking started!'), indicator: 'blue'});
                    }
                });
            }).addClass('btn-primary');
        }
        if (frm.doc.status === 'In Progress') {
            frm.add_custom_button(__('Complete Picking'), function() {
                frappe.call({
                    method: 'warehouse_3pl.warehouse_3pl.doctype.pick_task.pick_task.complete_pick',
                    args: { pick_name: frm.doc.name },
                    callback: function() {
                        frm.reload_doc();
                        frappe.show_alert({message: __('Pick complete! Pack Task created.'), indicator: 'green'});
                    }
                });
            }).addClass('btn-primary');
        }
        if (frm.doc.status === 'Complete') {
            frm.add_custom_button(__('Pack Task'), function() {
                frappe.set_route('List', 'Pack Task', {pick_task: frm.doc.name});
            }, __('View'));
        }
        if (frm.doc.client_order) {
            frm.add_custom_button(__('Client Order'), function() {
                frappe.set_route('Form', 'Client Order', frm.doc.client_order);
            }, __('View'));
        }
    }
});
