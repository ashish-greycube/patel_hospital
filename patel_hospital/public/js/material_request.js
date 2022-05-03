frappe.ui.form.on('Material Request', {
    refresh: function (frm) {
        if (frm.doc.docstatus == 1 && frm.doc.status != 'Stopped') {
            if (frm.doc.material_request_type === "Purchase") {
                frm.add_custom_button(__('Mutliple Purchase Order'),
                    () => frm.events.make_multiple_purchase_order(frm), __('Create'));
            }
        }
    },
    make_multiple_purchase_order: function (frm) {
        frappe.call({
            method: "patel_hospital.purchase_order_controller.make_multiple_purchase_order",
            frm: frm,
            args: {
                'source_name': frm.doc.name
            },
            run_link_triggers: true,
            freeze: true,
            callback: function (r) {
                if (r.message) {
                    let pos = r.message
                    for (let index = 0; index < pos.length; index++) {
                        const element = pos[index];
                        frappe.model.sync(element);
                        if (true) {
                            frappe.get_doc(
                                element.doctype,
                                element.name
                            ).__run_link_triggers = true;
                        }
                        if (element.supplier) {
                            // window.open(`/app/purchase-order/${frappe.router.slug(element.name.toUpperCase())}`, '_blank');
                            window.open(`/app/purchase-order/` + element.name.toUpperCase(), '_blank');
                        } else {
                            frappe.set_route("Form", element.doctype, element.name);
                        }
                    }
                }
            }
        })
    },
})