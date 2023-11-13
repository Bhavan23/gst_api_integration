
frappe.ui.form.on('GSTR 3B Report', {
	refresh: function (frm) {
		$('[data-label="Download%20JSON"]').hide()
		$('[data-label="View%20Form"]').hide()
		if (frm.doc.status == "Saved Successfully" && cur_frm.doc.workflow_state == "Saved") {
			frm.add_custom_button(__('RET STATUS'), () => {
				frappe.call({
					method: "gst_api_integration.gstr_3b_report_custom.gstr3b_status",
					args: { "doc_name": cur_frm.doc.name },
					async: false
				})
			})
		}
	},
	before_workflow_action: function (frm) {
		if (frm.doc.workflow_state == "Pending") {
			if (cur_frm.doc.json_output) {
				frappe.call(
					{
						method: "gst_api_integration.gstr_3b_report_custom.save_gstr3b",
						args: { "json_file": frm.doc.json_output, "month": frm.doc.month , "year": frm.doc.year},
						callback: (r) => {
							if (r.message) {
								if (res.message == 'RETOTPREQUEST') {
									frappe.throw({
										message: 'An OTP sent to registered mobile number/email. Please provide OTP',
										title: 'In just 10 minutes, OTP expired.'
									}
									)
									return 1
								}
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
		if (frm.doc.workflow_state == "Pending") {
			cur_frm.set_value('saved_headers', '{}').then(cur_frm.set_value('saved_response', '{}')).then(cur_frm.set_value('status', '')).then(cur_frm.save())
		}

		if (frm.doc.status == "Saved Successfully" && !cur_frm.doc.docstatus && !cur_frm.__islocal) {
			frappe.msgprint("GSTR3B saved successfully", "Status:[200]")
		}
	},
}); 
