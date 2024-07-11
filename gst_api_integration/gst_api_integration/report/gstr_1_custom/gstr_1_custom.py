# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json
from datetime import date

import frappe
from frappe import _
import json
import requests
from frappe.utils import flt, formatdate, getdate, get_datetime_str, cstr
from six import iteritems

from erpnext.regional.india.utils import get_gst_accounts

from random import randint
from frappe.utils import getdate, random_string, get_datetime_str
from gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report import get_access_token, create_api_log

from erpnext.regional.report.gstr_1.gstr_1 import Gstr1Report


ACTIONS = {
    "B2B": "B2B",
 	"B2C Large": "B2CL",
	"B2C Small": "B2CS",
 	"CDNR-REG": "CDNR",
 	"CDNR-UNREG": "CDNRA",
 	"EXPORT": "EXP",
 	"Advances": "AT",
 	"NIL Rated": "NIL"
}

def execute(filters=None):
	columns, datas =  Gstr1Report(filters).run()

	new_datas = []
	invoices = []
	if not datas: return
	if isinstance(datas[0],list) or isinstance(datas[0],tuple):
		action = filters.get('type_of_business')
		if filters.get('posted') or filters.get('not_posted'):
			invoices = get_posted_invoices(to_date=filters.get('to_date'), action= action) or []
		for data in datas:
			if filters.get('posted'):
				d = {column.get('fieldname'): data[i] for i, column in enumerate(columns)}
				if action == 'B2B':
					if d.get('invoice_number') in invoices:
						if not filter.get('include_fuel_invoices'):
							if not any(d.get('invoice_number', '').startswith(prefix) for prefix in ["FSINV-", "BPSI-", "IOSI-", "JISI-"]):
								new_datas.append(d)
						else:
							new_datas.append(d)
				if action == 'CDNR-REG':
					if d.get('invoice_number') in invoices:
						if not filter.get('include_fuel_invoices'):
							if not any(d.get('invoice_number', '').startswith(prefix) for prefix in ["FSINV-", "BPSI-", "IOSI-", "JISI-"]):
								new_datas.append(d)
						else:
							new_datas.append(d)

			elif filters.get('not_posted'):
				d = {column.get('fieldname'): data[i] for i, column in enumerate(columns)}
				if action == 'B2B':
					if d.get('invoice_number') not in invoices:
						if not filter.get('include_fuel_invoices'):
							if not any(d.get('invoice_number', '').startswith(prefix) for prefix in ["FSINV-", "BPSI-", "IOSI-", "JISI-"]):
								new_datas.append(d)
						else:
							new_datas.append(d)
				if action == 'CDNR-REG':
					if d.get('invoice_number') not in invoices:
						if not filter.get('include_fuel_invoices'):
							if not any(d.get('invoice_number', '').startswith(prefix) for prefix in ["FSINV-", "BPSI-", "IOSI-", "JISI-"]):
								new_datas.append(d)
						else:
							new_datas.append(d)

			else:
				d = {column.get('fieldname') : data[i]  for i, column in enumerate(columns) }
				if d.get('invoice_number'):
					if not filter.get('include_fuel_invoices'):
						if not any(d.get('invoice_number', '').startswith(prefix) for prefix in ["FSINV-", "BPSI-", "IOSI-", "JISI-"]):
							new_datas.append(d)
					else:
						new_datas.append(d)
	else:
		new_datas = datas

	return columns, new_datas

def get_posted_invoices(to_date=None, action= None):
	if not action:
		return

	action = ACTIONS.get(action)

	gst_integration_settings = frappe.get_single('GST Integration Settings')

	# GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type

	otp = gst_integration_settings.otp
	requestid = random_string(randint(10, 18))

	gstin = gst_integration_settings.gstin
	state_code = gstin[:2]

	ret_period = getdate(to_date).strftime("%m%Y")

	if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
		frappe.throw("GST Details Missing")

	access_token = get_access_token(gst_integration_settings, base_url)

	path = "/enriched/returns/gstr1"
	if gst_integration_settings.is_testing:
		path = "/test/enriched/returns/gstr1"

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

	response = requests.request("GET", url, params=params, headers=headers)

	create_api_log(response, action= cstr(action).upper())

	if response.ok:
		res = response.json()
		if res.get('errorCode') == 'RETOTPREQUEST':
			frappe.throw('<b style= "color: red;padding-bottom:10px">Your OTP has Expired</b><br>An OTP sent to registered mobile number/email. Please provide OTP','In just 10 minutes, OTP expired.')

		invoices = []
		if res.get(action.lower()):
			for ret_data in res[action.lower()]:
				if action.lower() == 'b2b':
					for data in ret_data.get('inv'):
						invoices.append(data.get('inum'))
				if action.lower() == 'cdnr':
					for data in ret_data.get('nt'):
						invoices.append(data.get('nt_num'))
	else:
		frappe.throw(response.text)

	return set(invoices)

@frappe.whitelist(allow_guest = True)
def create_record(datas, filters):
	from gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report import GSTR1Report as g1
	from erpnext.regional.report.gstr_1.gstr_1 import get_json

	field_map = {value: key for key , value in g1.field_map.items()}
	filters = json.loads(filters)
	datas = json.loads(datas)

	datas.append({})

	# validate existing document
	if filters.get('from_date'):
		exists = frappe.db.exists("GSTR 1 Report", {"to_date": ["between",[ filters.get('from_date'), filters.get('to_date')]], "type_of_business": filters.get('type_of_business')})
		if exists:
			frappe.throw("Already document exists for given period <b>{}</b><br>{}".format(
				filters.get('from_date'), exists), title="Document Already Exists")

		filters = {filter: filters.get(filter) for filter in filters if filters.get(filter)}

		convert_date_to_str(datas)

		json_data = None
		try:
			json_data = get_json(data=json.dumps(
				datas),	report_name='GSTR-1', filters=json.dumps(filters))
		except KeyError as e:
			frappe.throw(str(e).replace("'", '').replace("_", ' ').title(), title="Missing Value")
		except Exception as e:
			frappe.throw(str(e), "Error")

	if json_data:
		doc = frappe.new_doc('GSTR 1 Report')
		doc.company = filters.get('company')
		doc.company_address = filters.get('company_address')
		doc.company_gstin = filters.get('company_gstin')
		doc.from_date = filters.get('from_date')
		doc.to_date = filters.get('to_date')
		doc.type_of_business = field_map.get(filters.get('type_of_business'))
		doc.json_file = json.dumps(json_data.get("data"))
		doc.is_from_report = 1
		doc.save()

		if doc:
			frappe.msgprint("Record created Successfully")

def convert_date_to_str(datas):
	for data in datas:
		for key in data:
			if type(data.get(key)) is date:
				data[key] = get_datetime_str(data.get(key))
