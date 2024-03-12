# Copyright (c) 2023, aerele and contributors
# For license information, please see license.txt

import frappe
from erpnext.regional.report.gstr_2.gstr_2 import Gstr2Report

from gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report import get_access_token
from gst_api_integration.gst_api_integration.doctype.api_log.api_log import create_api_log
from random import randint
from frappe.utils import getdate, random_string, cstr, flt
from frappe import _
import json
import requests

ACTIONS = {
	"B2B": "B2B",
		"CDNR": "CDN"
	}

def execute(filters=None):
	global datas
	columns, datas = Gstr2Report(filters).run()
	action = ACTIONS.get(filters.get('type_of_business'))
	
	if filters.get('filed'):
		columns = get_gst_columns()
		datas = []
  
		for data in  get_gstr2_data(filters, action=ACTIONS.get(action)) or []:
			gstin = [data.get('ctin'),]
			for inv in data.get('inv'):
				idt = str(frappe.utils.getdate(inv.get('idt')))
				
				main_value = [
					inv.get('inum'), idt, flt(inv.get('val'), 2)
				]
				datas.append(gstin + main_value)

	return columns, datas

def filter_data(mapped_data, gst_data, filed):
	
	row_map = {row: data for row, data in enumerate(datas)}
 
	def get_value(data):
		data[1:2] = [None]
		return data

	with_out_invoice = [get_value(list(data)) for data in gst_data]
	
	for key in mapped_data:
		
		if filed:
			print(mapped_data[key] ,  gst_data)
			if mapped_data[key] not in gst_data:
				print(mapped_data[key],"\n",)
				if mapped_data[key] not in with_out_invoice:
					row_map.pop(key)
		else:
			if mapped_data[key] in gst_data:
				if mapped_data[key] in with_out_invoice:
					row_map.pop(key)
     
	return list(row_map.values())


def get_gstr2_data(filters, action):
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
		if res.get('status') == 200:
			return res.get(action.lower())
		else:
			frappe.throw(res.get('message'), title="BAD Response")
	else:
		frappe.throw("{}".format(response), title= "Api Error")



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
			"fieldname":"Date",
			"label": _("Date"),
			"fieldtype": "Date" 
		},
		{
			"fieldname":"amount",
			"label": _("Amount"),
			"fieldtype": "float" ,
			"width": "100px"
		},
	]        
	