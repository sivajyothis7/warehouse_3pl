frappe.ui.form.on('Rate Card', {
	setup(frm) {
		frm.set_query('client', function() {
			return { filters: { 'is_3pl_client': 1 } };
		});
	}
});
