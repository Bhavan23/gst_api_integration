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
		if (frm.doc.workflow_state == "Pending"){
			if (cur_frm.doc.json_file) {
				frappe.call(
					{
						method: "gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report.save_gstr1",
						args: { "doc_name": cur_frm.doc.name, "json_file": frm.doc.json_file, "gstin": frm.doc.company_gstin, "to_date": frm.doc.to_date },
						callback: (r) => {
							if (r.message) {
								if (r.message == 'RETOTPREQUEST'){
									frappe.throw({
										message:'<b style= "color: red;padding-bottom:10px">Your OTP has Expired</b><br>An OTP sent to registered mobile number/email. Please provide OTP',
										title: 'In just 10 minutes, OTP expired.'}
										)
										return	1
								}
							}
						},
						async: false
					}
				)
			}
		}
	},
	after_workflow_action: function (frm) {
		if (frm.doc.status == "Saved Successfully" && !cur_frm.doc.docstatus && !cur_frm.__islocal) {
			frappe.msgprint("GSTR1 saved successfully", "Status:[200]")
		}
	},
});
