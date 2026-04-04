frappe.ui.form.on('Warehouse Job Record', {
    setup(frm) {
        frm.set_query('client', function() {
            return { filters: { 'is_3pl_client': 1 } };
        });
    },
    refresh(frm) {
        // === OVERVIEW DASHBOARD ===
        if (!frm.is_new()) {
            frappe.call({
                method: 'warehouse_3pl.warehouse_3pl.doctype.warehouse_job_record.warehouse_job_record.get_job_dashboard_data',
                args: { job_name: frm.doc.name },
                callback: function(r) {
                    if (r.message) {
                        render_overview(frm, r.message);
                    }
                }
            });
        }

        // === ACTION BUTTONS ===
        if (!frm.is_new()) {
            // Create ASN
            if (!['Completed','Closed','Cancelled'].includes(frm.doc.job_status)) {
                frm.add_custom_button(__('Create ASN'), function() {
                    frappe.new_doc('ASN', {
                        client: frm.doc.client,
                        warehouse_job: frm.doc.name,
                    });
                }, __('Create'));

                frm.add_custom_button(__('Create Client Order'), function() {
                    frappe.new_doc('Client Order', {
                        client: frm.doc.client,
                        warehouse_job: frm.doc.name,
                    });
                }, __('Create'));
            }

            // View linked documents
            frm.add_custom_button(__('ASNs'), function() {
                frappe.set_route('List', 'ASN', {warehouse_job: frm.doc.name});
            }, __('View'));

            frm.add_custom_button(__('Receivings'), function() {
                frappe.set_route('List', 'Receiving', {warehouse_job: frm.doc.name});
            }, __('View'));

            frm.add_custom_button(__('Client Orders'), function() {
                frappe.set_route('List', 'Client Order', {warehouse_job: frm.doc.name});
            }, __('View'));

            frm.add_custom_button(__('Billing'), function() {
                frappe.set_route('List', 'Billing Transaction', {warehouse_job: frm.doc.name});
            }, __('View'));

            frm.add_custom_button(__('Delivery Notes'), function() {
                frappe.set_route('List', 'Delivery Note', {custom_warehouse_job: frm.doc.name});
            }, __('View'));
        }

        // === FETCH BUTTONS ===
        if (!frm.is_new()) {
            frm.fields_dict.fetch_vouchers && frm.fields_dict.fetch_vouchers.$input &&
            frm.fields_dict.fetch_vouchers.$input.off('click').on('click', function() {
                frm.call('fetch_linked_vouchers').then(() => {
                    frm.reload_doc();
                    frappe.show_alert({message: __('Vouchers fetched'), indicator: 'green'});
                });
            });
        }
    },

    client(frm) {
        if (frm.doc.client) {
            frappe.db.get_value('Customer', frm.doc.client,
                ['carrier_preferences', 'default_temp_zone', 'client_code'], function(r) {
                if (r && r.client_code) {
                    frm.set_value('branch', '');
                }
            });
        }
    }
});

function render_overview(frm, data) {
    var status_colors = {
        'Created': '#6c757d',
        'Confirmed': '#0d6efd',
        'In Progress': '#fd7e14',
        'Invoiced': '#6f42c1',
        'Completed': '#198754',
        'Closed': '#495057',
        'Cancelled': '#dc3545',
    };
    var status_color = status_colors[data.job_status] || '#6c757d';
    var gp_pct = data.total_revenue > 0 ? ((data.gross_profit / data.total_revenue) * 100).toFixed(1) : '0.0';
    var gp_color = data.gross_profit >= 0 ? '#198754' : '#dc3545';

    var html = `
    <div style="padding: 24px 20px;">
        <!-- Header -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:28px; padding-bottom:16px; border-bottom:1px solid #eee;">
            <div>
                <h3 style="margin:0 0 6px 0; font-size:20px;">${data.client_name || data.client}</h3>
                <span style="color:#6c757d; font-size:13px;">${frm.doc.name} &middot; ${data.date}</span>
            </div>
            <span style="background:${status_color}; color:#fff; padding:7px 18px; border-radius:20px; font-weight:600; font-size:13px;">
                ${data.job_status}
            </span>
        </div>

        <!-- KPI Cards -->
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; margin-bottom:28px;">
            <div style="background:#f8f9fa; border-radius:10px; padding:20px 16px; text-align:center; border-left:4px solid #0d6efd;">
                <div style="font-size:26px; font-weight:700; color:#0d6efd;">${data.total_in_qty}</div>
                <div style="color:#6c757d; font-size:12px; margin-top:6px; text-transform:uppercase; letter-spacing:0.5px;">Stock In</div>
            </div>
            <div style="background:#f8f9fa; border-radius:10px; padding:20px 16px; text-align:center; border-left:4px solid #fd7e14;">
                <div style="font-size:26px; font-weight:700; color:#fd7e14;">${data.total_out_qty}</div>
                <div style="color:#6c757d; font-size:12px; margin-top:6px; text-transform:uppercase; letter-spacing:0.5px;">Stock Out</div>
            </div>
            <div style="background:#f8f9fa; border-radius:10px; padding:20px 16px; text-align:center; border-left:4px solid #198754;">
                <div style="font-size:26px; font-weight:700; color:#198754;">${format_currency(data.total_revenue)}</div>
                <div style="color:#6c757d; font-size:12px; margin-top:6px; text-transform:uppercase; letter-spacing:0.5px;">Revenue</div>
            </div>
            <div style="background:#f8f9fa; border-radius:10px; padding:20px 16px; text-align:center; border-left:4px solid ${gp_color};">
                <div style="font-size:26px; font-weight:700; color:${gp_color};">${format_currency(data.gross_profit)}</div>
                <div style="color:#6c757d; font-size:12px; margin-top:6px; text-transform:uppercase; letter-spacing:0.5px;">Gross Profit (${gp_pct}%)</div>
            </div>
        </div>

        <!-- Linked Document Badges -->
        <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:24px;">
            ${make_badge('ASN', data.counts.asn, '#0d6efd', 'ASN', {warehouse_job: frm.doc.name})}
            ${make_badge('Receiving', data.counts.receiving, '#198754', 'Receiving', {warehouse_job: frm.doc.name})}
            ${make_badge('Orders', data.counts.client_order, '#fd7e14', 'Client Order', {warehouse_job: frm.doc.name})}
            ${make_badge('Billing', data.counts.billing, '#6f42c1', 'Billing Transaction', {warehouse_job: frm.doc.name})}
            ${make_badge('Delivery Notes', data.counts.delivery_note, '#dc3545', 'Delivery Note', {custom_warehouse_job: frm.doc.name})}
        </div>

        <!-- Balance Bar -->
        <div style="padding:16px 20px; background:linear-gradient(135deg, #e8f5e9, #f1f8e9); border-radius:10px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:600; color:#2e7d32; font-size:14px;">Balance in Warehouse</span>
            <span style="font-size:20px; font-weight:700; color:#198754;">${data.balance_qty} units</span>
        </div>
    </div>`;

    // Set the HTML field
    if (frm.fields_dict.overview_html) {
        frm.fields_dict.overview_html.$wrapper.html(html);
    }
}

function make_badge(label, count, color, doctype, filters) {
    var filter_str = Object.entries(filters).map(([k,v]) => k + '=' + encodeURIComponent(v)).join('&');
    return `<a href="/app/${frappe.router.slug(doctype)}?${filter_str}"
        style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; background:#fff; border:1px solid #dee2e6; border-radius:20px; text-decoration:none; color:#333; font-size:13px;">
        <span style="background:${color}; color:#fff; border-radius:50%; width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center; font-size:11px; font-weight:700;">${count}</span>
        ${label}
    </a>`;
}
