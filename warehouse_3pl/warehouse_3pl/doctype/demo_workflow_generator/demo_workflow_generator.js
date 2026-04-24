frappe.ui.form.on("Demo Workflow Generator", {
    refresh(frm) {
        frm.add_custom_button(__("Generate Demo"), () => {
            frappe.confirm(
                __("This will create a demo Customer, Items, Warehouses, Rate Card, and drive a full ASN → Receiving → Putaway → Client Order → Wave → Pick → Pack → Delivery Note. Existing records are reused. Continue?"),
                () => _run_demo(frm),
            );
        }).addClass("btn-primary");

        if (frm.doc.last_run_status === "Success") {
            frm.dashboard.set_headline_alert(
                __("Last run: <b>Success</b> at {0}", [frappe.datetime.str_to_user(frm.doc.last_run_at)]),
                "green",
            );
        } else if (frm.doc.last_run_status === "Failed") {
            frm.dashboard.set_headline_alert(
                __("Last run: <b>Failed</b> at {0} — see log below", [frappe.datetime.str_to_user(frm.doc.last_run_at)]),
                "red",
            );
        }
    },
});

function _run_demo(frm) {
    frappe.dom.freeze(__("Generating demo workflow — this may take a few seconds..."));
    frappe
        .call({
            method: "warehouse_3pl.warehouse_3pl.doctype.demo_workflow_generator.demo_workflow_generator.run_demo",
        })
        .then((r) => {
            frappe.dom.unfreeze();
            if (r && r.message && r.message.ok) {
                const created = r.message.created || {};
                frappe.msgprint({
                    title: __("Demo generated"),
                    indicator: "green",
                    message: _format_created(created),
                });
                frm.reload_doc();
            }
        })
        .catch(() => {
            frappe.dom.unfreeze();
            frm.reload_doc();
        });
}

function _format_created(c) {
    const row = (label, value) => {
        if (!value) return "";
        const v = Array.isArray(value) ? value.join(", ") : value;
        return `<tr><td style="padding:3px 10px 3px 0;"><b>${label}</b></td><td>${frappe.utils.escape_html(v)}</td></tr>`;
    };
    return `<table>
        ${row("Customer", c.customer)}
        ${row("Items", c.items)}
        ${row("Warehouses", c.warehouses)}
        ${row("Rate Card", c.rate_card)}
        ${row("ASN", c.asn)}
        ${row("Receiving", c.receiving)}
        ${row("Putaway Tasks", c.putaway_tasks)}
        ${row("Client Order", c.client_order)}
        ${row("Wave", c.wave)}
        ${row("Pick Task", c.pick_task)}
        ${row("Pack Task", c.pack_task)}
        ${row("Delivery Note", c.delivery_note)}
    </table>`;
}
