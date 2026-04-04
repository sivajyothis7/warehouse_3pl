frappe.ui.form.on('Client Order', {
    setup(frm) {
        frm.set_query('client', function() {
            return { filters: { 'is_3pl_client': 1 } };
        });
    },
    warehouse_job(frm) {
        if (frm.doc.warehouse_job && !frm.doc.client) {
            frappe.db.get_value('Warehouse Job Record', frm.doc.warehouse_job, 'client', function(r) {
                if (r && r.client) {
                    frm.set_value('client', r.client);
                }
            });
        }
    },
    refresh(frm) {
        if (frm.doc.docstatus === 1 && ['Confirmed','Allocated'].includes(frm.doc.status)) {
            frm.add_custom_button(__('Create Wave'), function() {
                frappe.new_doc('Wave', {
                    wave_date: frappe.datetime.get_today(),
                    picking_strategy: 'Single Order',
                    orders: [{client_order: frm.doc.name}]
                });
            }, __('Actions'));
        }
        if (['Picking','Packing','Shipped'].includes(frm.doc.status)) {
            frm.add_custom_button(__('Pick Tasks'), function() {
                frappe.set_route('List', 'Pick Task', {client_order: frm.doc.name});
            }, __('View'));
            frm.add_custom_button(__('Pack Tasks'), function() {
                frappe.set_route('List', 'Pack Task', {client_order: frm.doc.name});
            }, __('View'));
        }
    },
    client(frm) {
        if (frm.doc.client) {
            frappe.db.get_value('Customer', frm.doc.client, ['carrier_preferences'], function(r) {
                if (r && r.carrier_preferences) {
                    frm.set_value('carrier_preference', r.carrier_preferences);
                }
            });
        }
    }
});
