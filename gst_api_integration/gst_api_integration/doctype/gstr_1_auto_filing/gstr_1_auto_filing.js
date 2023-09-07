// Copyright (c) 2023, aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('GSTR 1 Auto Filing', {
	refresh: function (frm) {
		frm.set_value("company", frappe.defaults.get_user_default("Company"))
		if (!["Saved Successfully", "Proceeded", "Succesfully Filed"].includes(cur_frm.doc.status) && !cur_frm.doc.__islocal){
			frm.add_custom_button(__('RET SAVE'), () => {
				if (cur_frm.doc.json_file) {
					frappe.call(
						{
							method: "gst_api_integration.gst_api_integration.doctype.gstr_1_auto_filing.gstr_1_auto_filing.save_gstr1",
							args: { "json_file": frm.doc.json_file, "gstin": frm.doc.company_gstin, "to_date": frm.doc.to_date },
							callback: (r)=>{
								if (r.message){
									cur_frm.set_value('saved_headers', r.message.headers)
									cur_frm.set_value('saved_response', r.message.res)
									cur_frm.set_value('status', r.message.status)
									cur_frm.save()
									cur_frm.refresh_fields()
									frappe.show_alert({ message: __(r.message.msg), indicator: r.message.status === 'Failed' ? "red" : "green" }, 7);
								}
							},
							async:false
						}
					)
				}
			}, __("Actions"))
		}
		if (cur_frm.doc.status === "Saved Successfully") {
			frm.add_custom_button(__('RET STATUS'), () => {
				frappe.call(
					{
						method: "gst_api_integration.gst_api_integration.doctype.gstr_1_auto_filing.gstr_1_auto_filing.gstr1_status",
						args: { "doc_name": cur_frm.doc.name },
						callback: (r) => {
							if (r.message) {
								frappe.show_alert({message: __(res.get('message')), indicator:"green"})
							}
						},
						async: false
					}
				)
			}, __("Actions"))
			frm.add_custom_button(__('PROCEED TO FILE'), ()=> {
					frappe.call(
						{
							method: "gst_api_integration.gst_api_integration.doctype.gstr_1_auto_filing.gstr_1_auto_filing.proceed_to_file",
							args: { "doc_name": cur_frm.doc.name },
							callback: (r) => {
								if (r.message) {
									cur_frm.set_value('submited_headers', r.message.headers)
									cur_frm.set_value('submited_payload', r.message.paload)
									cur_frm.set_value('submited_response', r.message.res)
									cur_frm.set_value('status', r.message.status)
									cur_frm.save()
									frappe.show_alert({ message: __(r.message.msg), indicator: r.message.status === 'Failed' ? "red" : "green" }, 7);
								}
							},
							async: false
						}
					)
				}
			, __("Actions"))
	}
	if (cur_frm.doc.status === "Proceeded" ) {
		frm.add_custom_button(__('FILE'), () => {
			if (cur_frm.doc.json_file) {
				frappe.call({
					method: "gst_api_integration.gst_api_integration.doctype.gstr_1_auto_filing.gstr_1_auto_filing.send_otp",
					args: { "doc_name": cur_frm.doc.name },
					callback: (r) => {
						console.log(r.message)
						if(r.message === 1){
							let d = new frappe.ui.Dialog({
								title: __('OTP sent for Register Mobile number'),
								fields: [
									{
										fieldtype: "Int",
										label: __("Enter Your OTP"),
										fieldname: "otp",
										reqd: 1
									}
								],
								primary_action: function () {
									let data = d.get_values();
									d.hide();
									frappe.call({
										method: 'gst_api_integration.gst_api_integration.doctype.gstr_1_auto_filing.gstr_1_auto_filing.file_gstr1',
										args: {
											"doc_name": frm.doc.name,
											"otp": data.otp
										},
										freeze: true,
										callback: function (r) {
											cur_frm.set_value('filed_headers', r.message.headers)
											cur_frm.set_value('filed_response', r.message.res)
											cur_frm.set_value('reference_id', r.message.reference_id)
											cur_frm.set_value('status', r.message.status)
											cur_frm.save("Submit")
											frappe.show_alert({ message: __(r.message.msg), indicator: r.message.status === 'Failed' ? "red" : "green" }, 7);
											frm.reload_doc();
										}
									});
								},
							});
							d.show()
						}
					},
					async: false
				}
				)
			}
		}, __("Actions"))
	}
},
	setup: function (frm) {
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
	},
});
