frappe.ui.form.on('Wave', {
    refresh(frm) {
        if (frm.doc.status === 'Planning' && !frm.is_new()) {
            frm.add_custom_button(__('Release Wave'), function() {
                frappe.call({
                    method: 'warehouse_3pl.warehouse_3pl.doctype.wave.wave.release_wave',
                    args: { wave_name: frm.doc.name },
                    callback: function() {
                        frm.reload_doc();
                        frappe.show_alert({message: __('Wave released! Pick Tasks created.'), indicator: 'green'});
                    }
                });
            }).addClass('btn-primary');
        }
        if (['Released','In Progress'].includes(frm.doc.status)) {
            frm.add_custom_button(__('Pick Tasks'), function() {
                frappe.set_route('List', 'Pick Task', {wave: frm.doc.name});
            }, __('View'));
        }
    }
});
