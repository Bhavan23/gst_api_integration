# Copyright (c) 2023, aerele and contributors
# For license information, please see license.txt

import frappe
from erpnext.regional.report.gstr_2.gstr_2 import Gstr2Report

from gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report import get_access_token
from gst_api_integration.gst_api_integration.doctype.api_log.api_log import create_api_log
from random import randint
from frappe.utils import getdate, random_string, cstr, flt, cint
from frappe import _
import json
import requests

ACTIONS = {
	"B2B": "B2B",
		"CDNR": "CDN"
	}

def execute(filters=None):
	try:
		columns, datas = Gstr2Report(filters).run()
	except Exception as e:
		if "no attribute 'tax_details'" in cstr(e):
			frappe.throw("Selct Different Date", title= "Invalid Date")

	action = ACTIONS.get(filters.get('type_of_business'))
	
	portal_data = []
	if filters.get('record_from') != 'System Data':
		portal_data = get_portal_data(filters, action=ACTIONS.get(action))

	gstins = [data[0] for data in get_gst_formated_data(portal_data)]
	invoices = [data[1] for data in get_gst_formated_data(portal_data)]

	if not filters.get('record_from'):
		if filters.get('filed'):
			datas = filter_filed_data(gstins, invoices, datas)
		else:
			filed_data = filter_filed_data(gstins, invoices, datas)
			for data in filed_data:
				datas.remove(data)

		return columns, datas
	else:
		if filters.get('record_from') == 'Portal Data':
			columns = get_gst_columns()
			datas = []
			for data in  get_portal_data(filters, action=ACTIONS.get(action)) or []:
				gstin = [data.get('ctin'),]
				for inv in data.get('inv'):
					idt = str(frappe.utils.getdate(inv.get('idt')))

					main_value = [
						inv.get('inum'), idt, flt(inv.get('val'), 2)
					]
					datas.append(gstin + main_value)

		return columns, datas

def filter_filed_data(gstins, invoices, system_data):
	filed = False
	filed_data = []
	for data in system_data:
		if data[0] in gstins:
			filed = True
		if filed:
			if bill_no:=check_exists(data[1]):
				if bill_no in invoices:
					filed = True
				else:
					for invoice in invoices:
						if  invoice in bill_no:
							filed = True
							break
					else:
						filed = False
			else:
				filed = False
		if filed:
			filed_data.append(data)

	return filed_data
def get_gst_formated_data(datas):
	new_datas = []
	for data in  datas:
			gstin = data.get('ctin')
			for inv in data.get('inv'):
				new_datas.append([gstin, inv.get('inum')])
    
	return new_datas


def check_exists(invoice_no):
	if frappe.db.get_value("Purchase Invoice", invoice_no, 'bill_no'):
		return frappe.db.get_value("Purchase Invoice", invoice_no , 'bill_no')

def get_portal_data(filters, action):
	gst_integration_settings = frappe.get_single('GST Integration Settings')

	# GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type

	otp = gst_integration_settings.otp
	requestid = random_string(randint(8, 16))
	gstin = None
	if gstin:
		state_code = gstin[:2]
	else:
		gstin = gst_integration_settings.gstin
		state_code = gstin[:2]

	ret_period = getdate(filters.get("to_date")).strftime("%m%Y")

	if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
		frappe.throw("GST Details Missing")

	access_token = get_access_token(gst_integration_settings, base_url)

	path = "/enriched/returns/gstr2a"
	if gst_integration_settings.is_testing:
		path = "/test/enriched/returns/gstr2a"

	url = base_url + path

	params = {
		"action": cstr(action).upper(),
		"gstin": gstin,
		"ret_period": ret_period
	}

	headers = {
			'username':  user_name,
			'state-cd': state_code,
			'otp': otp,
			'Content-Type': content_type,
			'requestid': requestid,
			'gstin': gstin,
			'ret_period': ret_period,
			'Authorization': "Bearer " + access_token
		}

	response = requests.request(
		"GET", url, params=params, headers=headers )

	create_api_log(response, action="GSTR2 " + action)

	if response.ok:
		res = response.json()
		if cint(res.get('status')) == 200:
			return res.get(action.lower())
		else:
			frappe.msgprint(res.get('message'), title="BAD Response")
	else:
		frappe.throw("{}".format(cstr(response.json().get('error_description'))), title= "Api Error")

def get_gst_columns():
	return [
		{
			"fieldname":"gstin",
			"label": _("GSTIN of Supplier"),
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname":"invoice",
			"label": _("Invoice"),
			"fieldtype": "Data" 
		},
		{
			"fieldname":"date",
			"label": _("Date"),
			"fieldtype": "Date" 
		},
		{
			"fieldname":"amount",
			"label": _("Amount"),
			"fieldtype": "Float" ,
			"precision": 2,
			"width": "100px",
			"width": 200
		},
	]
	