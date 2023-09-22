frappe.listview_settings["GSTR 3B Report"] = {
	onload: function (listview) {
		listview.page.add_inner_button(__("RETSUBMIT"), () => {
			frappe.prompt({
				fieldtype: 'Data',
				label: __('Return Period'),
				fieldname: 'ret_period',
				description: "FORMAT : {month}{year}<br>EXAMPLE: 092023"
			}, (data) => {
				frappe.call({
					method: "gst_api_integration.gstr_3b_report_custom.submit_gstr3b",
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
					method: "gst_api_integration.gstr_3b_report_custom.ret_summary",
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

		listview.page.add_inner_button(__("RET FILE"), () =>
			frappe.prompt({
				fieldtype: 'Data',
				label: __('Return Period'),
				fieldname: 'ret_period',
				description: "FORMAT : {month}{year}<br>EXAMPLE: 092023"
			}, (data) => {
				frappe.call({
					method: "gst_api_integration.gstr_3b_report_custom.file_gstr3b",
					freeze: true,
					args: {
						ret_period: data.ret_period,
					},
					callback: (r) => {
						frappe.show_alert({ message: __(r.message.msg), indicator: r.message.status === 'Failed' ? "red" : "green" }, 7);
					}
				});
			}, __("File GSTR3B"), __('File')),
			__("Actions"));
	},
}
