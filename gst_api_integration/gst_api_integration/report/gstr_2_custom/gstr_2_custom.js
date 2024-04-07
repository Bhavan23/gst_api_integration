// Copyright (c) 2023, aerele and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GSTR-2-Custom"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"width": "80",
			change: function(){
				var from_date = new Date(frappe.query_report.get_filter_value('from_date')); 

				var year = from_date.getFullYear()
				var month = from_date.getMonth(); 

				var to_date = new Date(year, month + 1, 0);

				frappe.query_report.set_filter_value('to_date', to_date)
			}
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"read_only": 1
		},
		{
			"fieldname":"type_of_business",
			"label": __("Type of Business"),
			"fieldtype": "Select",
			"reqd": 1,
			"options": ["B2B","CDNR"],
			"default": "B2B"
		},
		{
			"fieldname":"record_from",
			"label": __("Show"),
			"fieldtype": "Select",
			"default": "System Data",
			"options":['', 'System Data', 'Portal Data']
		},
		{
			"fieldname":"filed",
			"label": __("Filed"),
			"fieldtype": "Check",
			change: function(){
				frappe.query_report.set_filter_value('record_from', '')
			},
		}
	]
};
