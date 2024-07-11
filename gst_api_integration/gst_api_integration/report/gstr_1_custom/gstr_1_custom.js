// Copyright (c) 2023, aerele and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GSTR-1-Custom"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "company_address",
			"label": __("Address"),
			"fieldtype": "Link",
			"options": "Address",
			"reqd": 1,
			"get_query": function () {
				let company = frappe.query_report.get_filter_value('company');
				if (company) {
					return {
						"query": 'frappe.contacts.doctype.address.address.address_query',
						"filters": { link_doctype: 'Company', link_name: company }
					};
				}
			}
		},
		{
			"fieldname": "company_gstin",
			"label": __("Company GSTIN"),
			"reqd": 1,
			"fieldtype": "Select"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
			"width": "80"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "type_of_business",
			"label": __("Type of Business"),
			"fieldtype": "Select",
			"reqd": 1,
			"options": [
				{ "value": "B2B", "label": __("B2B Invoices - 4A, 4B, 4C, 6B, 6C") },
				{ "value": "B2C Large", "label": __("B2C(Large) Invoices - 5A, 5B") },
				{ "value": "B2C Small", "label": __("B2C(Small) Invoices - 7") },
				{ "value": "CDNR-REG", "label": __("Credit/Debit Notes (Registered) - 9B") },
				{ "value": "CDNR-UNREG", "label": __("Credit/Debit Notes (Unregistered) - 9B") },
				{ "value": "EXPORT", "label": __("Export Invoice - 6A") },
				{ "value": "Advances", "label": __("Tax Liability (Advances Received) - 11A(1), 11A(2)") },
				{ "value": "NIL Rated", "label": __("NIL RATED/EXEMPTED Invoices") }
			],
			"default": "B2B"
		},
		{
			"fieldname": "not_posted",
			"label": __("Not Posted Only"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "posted",
			"label": __("Posted Only"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "include_fuel_invoices",
			"label": __("Include Fuel Invoices"),
			"fieldtype": "Check"
		}
	],
	after_datatable_render: table_instance => {
		window.setTimeout(
			()=>{
				$(`[data-label="Create%20Card"]`).hide()
				$(`[class="btn btn-default btn-sm ellipsis"]`).hide()
			},1000
		)
		
		if (frappe.query_report.get_values().not_posted) {
			$(`[data-label="Create%20Record"]`).show()
		}
		
		if (frappe.query_report.get_values().posted) {
			$(`[data-label="Create%20Record"]`).hide()
		}
		
		frappe.query_report.datatable.options.checkboxColumn = true
	},
	
	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true
		});
	},
	
	onload: function (report) {
		window.setTimeout(
			() => {
				$(`[data-label="Create%20Card"]`).hide()
				$(`[class="btn btn-default btn-sm ellipsis"]`).hide()
			}, 1000
		)
		
		let filters = report.get_values();

		frappe.call({
			method: 'erpnext.regional.report.gstr_1.gstr_1.get_company_gstins',
			args: {
				company: filters.company
			},
			callback: function (r) {
				frappe.query_report.page.fields_dict.company_gstin.df.options = r.message;
				frappe.query_report.page.fields_dict.company_gstin.refresh();
			}
		});
		
		report.page.add_inner_button(__("Create Record"), function () {
			let filters = report.get_values();
			
			const visible_idx = report.datatable.rowmanager.getCheckedRows().map(i => Number(i));
			if (visible_idx.length == 0) {
				frappe.throw("Please Select a row for Make Record")
			}
			var selected_rows = [];
			let indexes = report.datatable.rowmanager.getCheckedRows();
			for (let row = 0; row < indexes.length; ++row) {
				selected_rows.push(report.data[indexes[row]]);
			}

			frappe.call({
				method: 'gst_api_integration.gst_api_integration.report.gstr_1_custom.gstr_1_custom.create_record',
				args: {
					datas: selected_rows,
					filters: filters
				},
				callback: function (r) {
					if (r.message) {
						frappe.throw(_(r.message))
					}
				}
			});
		});
		
		report.page.add_inner_button(__("GSTR1 - Report List"), function () {
			frappe.set_route("Form", "GSTR 1 Report");
		});
	}
}


