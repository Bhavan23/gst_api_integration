// Copyright (c) 2023, aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('GST Integration Settings', {
	refresh: function(frm) {
		if (!cur_frm.doc.is_testing) {
			frm.add_custom_button(__('GET OTP'), () => {
				frappe.call(
					{
						method: "gst_api_integration.gst_api_integration.doctype.gstr_1_auto_filing.gstr_1_auto_filing.send_otp",
						callback: (r) => {
							if (r.message === 1) {
								frappe.show_alert({ message: __("An OTP sent to registered mobile number/email. Please provide OTP"), indicator: "green" })
							}
						},
						async: false
					}
				)
			}, __("Actions"))
		}
	},
	is_testing: function(frm){
		if (cur_frm.doc.is_testing){
			frm.set_value("otp","575757" )
		}
		else{
			frappe.show_alert({ message: __("Generate OTP"), indicator: "orange" })
			frm.set_value("otp", "")
		}
		cur_frm.save().then(cur_frm.reload_doc())
	}
});
