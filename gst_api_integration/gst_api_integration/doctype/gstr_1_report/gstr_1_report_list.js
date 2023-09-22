frappe.listview_settings["GSTR 1 Report"] = {
	onload: function (listview){
		listview.page.add_inner_button(__("PROCEEDTOFILE"),	() =>{
			frappe.prompt({
				fieldtype: 'Data',
				label: __('Return Period'),
				fieldname: 'ret_period',
				description: "FORMAT : {month}{year}<br>EXAMPLE: 092023"
				}, (data) => {
					frappe.call({
						method: "gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report.proceed_to_file",
						freeze: true,
						args: {
							ret_period: data.ret_period,
						},
						callback: (r) => {
							frappe.show_alert({ message: __(r.message.msg), indicator: r.message.status === 'Failed' ? "red" : "green" }, 7);
						}
					});
				}, __("Submited record can't be edit"), __('Submit'))
			},
		__("Actions"));
		
		listview.page.add_inner_button(__("RETSUMMARY"), () => {
			frappe.prompt({
				fieldtype: 'Data',
				label: __('Return Period'),
				fieldname: 'ret_period',
				description: "FORMAT : {month}{year}<br>EXAMPLE: 092023"
				}, (data) => {
					frappe.call({
						method: "gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report.ret_summary",
						freeze: true,
						args: {
							ret_period: data.ret_period,
						},
						callback: (r) => {
							frappe.show_alert({ message: __(r.message.msg), indicator: r.message.status === 'Failed' ? "red" : "green" }, 7);
						}
					});
			}, __("Check return summary"), __('View'))
			},
		__("Actions"));
		
		listview.page.add_inner_button(__("EVC FILE"), () => {
			frappe.call({
				method: "gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report.generate_otp",
				callback: (r) => {
					if (r.message === 1) {
						frappe.prompt([{
							fieldtype: 'Data',
							label: __('Return Period'),
							fieldname: 'ret_period',
							description: "FORMAT : {month}{year}<br>EXAMPLE: 092023"
							},
							{
								fieldtype: "Int",
								label: __("Enter Your OTP"),
								fieldname: "otp",
								reqd: 1
							}], (data) => {
								frappe.call({
									method: "gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report.file_gstr1",
									freeze: true,
									args: {
										ret_period: data.ret_period,
										evc_otp: data.otp 
									},
									callback: (r) => {
										frappe.show_alert({ message: __(r.message.msg), indicator: r.message.status === 'Failed' ? "red" : "green" }, 7);
									}
								});
						}, __("OTP sent to Register Mobile\Email"), __('File'))
					}
				},
				async: false
			})
		},
		__("Actions"));
	},
}
