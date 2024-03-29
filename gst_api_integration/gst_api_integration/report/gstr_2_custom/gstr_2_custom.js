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
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
			"width": "80"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
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
			"fieldname":"filed",
			"label": __("Filed only"),
			"fieldtype": "Check"
		},
		{
			"fieldname":"not_filed",
			"label": __("Not Filed Only"),
			"fieldtype": "Check"
		}
	]
};
