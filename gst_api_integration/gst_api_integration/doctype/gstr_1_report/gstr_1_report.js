// Copyright (c) 2023, aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('GSTR 1 Report', {
	refresh: function (frm) {
		frm.set_query('company_address', function (doc) {
			if (!doc.company) {
				frappe.throw(__('Please set Company'));
			}

			return {
				query: 'frappe.contacts.doctype.address.address.address_query',
				filters: {
					link_doctype: 'Company',
					link_name: doc.company
				}
			};
		});
		if (frm.doc.status == "Saved Successfully" && cur_frm.doc.workflow_state == "Saved"){
			frm.add_custom_button(__('RET STATUS'), () => {
				frappe.call({
					method: "gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report.gstr1_status",
					args: { "doc_name": cur_frm.doc.name },
					async: false
				})
			})
		}
	},
	before_workflow_action: function(frm){
		if (frm.doc.workflow_state == "Draft"){
			if (cur_frm.doc.json_file) {
				frappe.call(
					{
						method: "gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report.save_gstr1",
						args: { "json_file": frm.doc.json_file, "gstin": frm.doc.company_gstin, "to_date": frm.doc.to_date },
						callback: (r) => {
							if (r.message) {
								cur_frm.set_value('saved_headers', r.message.headers)
								cur_frm.set_value('saved_response', r.message.res)
								cur_frm.set_value('status', r.message.status)
							}
						},
						async: false
					}
				)
			}
		}
	},
	after_workflow_action: function (frm) {
		if (frm.doc.workflow_state == "Draft"){
			cur_frm.set_value('saved_headers', '{}').then(cur_frm.set_value('saved_response', '{}')).then(cur_frm.set_value('status', '')).then(cur_frm.save())
		}
		
		if (frm.doc.status == "Saved Successfully" && !cur_frm.doc.docstatus && !cur_frm.__islocal) {
			frappe.msgprint("GSTR1 saved successfully", "Status:[200]")
		}
	},
});
