import frappe
import json
import requests
from frappe.utils import getdate

from frappe.utils import random_string
from random import randint

from gst_api_integration.gst_api_integration.doctype.api_log.api_log import create_api_log

#access token
def get_access_token(gst_integration_settings= None, base_url= None, id= None, key= None):
	gst_integration_settings = frappe.get_single('GST Integration Settings') if not gst_integration_settings else gst_integration_settings
	
	base_url = gst_integration_settings.base_url if not base_url else base_url
	id = gst_integration_settings.client_id if not id else id
	key = gst_integration_settings.get_password("client_secret") if not key else key
	
	url = base_url + r"/gsp/authenticate?grant_type=token"
	
	headers = {
		'gspappid': id,
		'gspappsecret': key
	}
	response = requests.request("POST", url, headers=headers)
	
	create_api_log(response, action= "token")
	
	if response.ok:
		return response.json().get("access_token")
	else:
		frappe.throw(response.json().get("error_description"), title= "Failed")

@frappe.whitelist()
def save_gstr3b(json_file, month, year):
	month_no = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }.get(month)
	
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
	otp = gst_integration_settings.otp
	requestid = random_string(randint(8,16))
	
	gstin = gst_integration_settings.gstin
	state_code = gstin[:2]
	
	ret_period = str(month_no).zfill(2) + str(year)
		
	if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
		frappe.throw("GST Details Missing")
	
	access_token = get_access_token(gst_integration_settings, base_url)
			
	path = "/enriched/returns/gstr3b?action=RETSAVE"
	if gst_integration_settings.is_testing:
		path = "/test/enriched/returns/gstr3b?action=RETSAVE"
		
	url = base_url + path
	
	payload = json_file
	
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
	
	response = requests.request("PUT", url, headers=headers, data= payload)
	
	create_api_log(response, action= "RETSAVE")
	
	if response.ok:
		res = response.json()
		headers.pop('Authorization')
		headers.pop('otp')
		if res:
			if res.get('status') == 200:
				return {'headers': json.dumps(headers), 'res' : json.dumps(res), 'status': 'Saved Successfully', 'msg': res.get('message')}
			else:
				return {'headers': json.dumps(headers), 'res' : json.dumps(res), 'status': 'Failed', 'msg': res.get('message')}
	else:
		res = response.json()
		return {'headers': json.dumps(headers), 'res' : json.dumps(res), 'status': 'Failed', 'msg':res.get('message')}

	
@frappe.whitelist()
def gstr3b_status(doc_name):
	doc = frappe.get_doc("GSTR 3b Report", doc_name)
	
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
	otp = gst_integration_settings.otp
	saved_data = json.loads(doc.saved_headers)
	requestid = saved_data.get('requestid')
	
	gstin = doc.company_gstin
	if gstin:
		state_code = gstin[:2] 
	else:
		gstin = gst_integration_settings.gstin
		state_code = gstin[:2]
	
	ret_period = gst_integration_settings.ret_period
	if doc.to_date:
		ret_period = getdate(doc.to_date).strftime("%m%Y")
		
	if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
		frappe.throw("GST Details Missing")
		
	access_token = get_access_token(gst_integration_settings, base_url)
	
	path = "/enriched/returns?action=RETSTATUS&gstin={}&ret_period={}".format(gstin, ret_period)
	if gst_integration_settings.is_testing:
		path = "/test/enriched/returns?action=RETSTATUS&gstin={}&ret_period={}".format(gstin, ret_period)
		
	url = base_url + path
	
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
		
	response = requests.request("GET", url, headers=headers)
	
	create_api_log(response, action= "RETSTATUS")
	
	if response.ok:
		res = response.json()
		if res.get("error_report"):
			frappe.msgprint(json.dumps(res.get("error_report")), title= "Error Report")
		else:
			frappe.msgprint(response.text)
	else:
		frappe.msgprint("Failed")
	
@frappe.whitelist()
def submit_gstr3b(ret_period= None):
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
	otp = gst_integration_settings.otp
	requestid = random_string(randint(8,16))
	
	gstin = gst_integration_settings.gstin
	state_code = gstin[:2]
	
	ret_period = ret_period
		
	if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
		frappe.throw("GST Details Missing")
	
	access_token = get_access_token(gst_integration_settings, base_url)
	path = r"/enriched/returns/gstr3b?action=RETSUBMIT"
	if gst_integration_settings.is_testing:
		path = r"/test/enriched/returns/gstr3b?action=RETSUBMIT"
		
	url = base_url + path
	
	payload = {
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
		'Authorization': "Bearer " + access_token,
		'rtn_typ': 'GSTR3B',
		'userrole': 'GSTR3B'
		
}
	response = requests.request("POST", url, headers=headers, data= json.dumps(payload))
	
	create_api_log(response, action= "RETSUBMIT")
	
	if response.ok:
		headers.pop('Authorization')
		headers.pop('otp')
		res = response.json()
		if res:
			if res.get('status') == 200:
				return {
					"msg": res.get('message')
				}
			else:
				frappe.throw(res.get('message'), title= "Failed")
	else:
		res = response.json()
		frappe.throw(res.get('error_description'), title="Error")
		
@frappe.whitelist()
def ret_summary(ret_period= None):
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
	otp = gst_integration_settings.otp
	requestid = random_string(randint(8,16))
	
	gstin = gst_integration_settings.gstin
	state_code = gstin[:2]
	
	ret_period = ret_period
		
	if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
		frappe.throw("GST Details Missing")
	
	access_token = get_access_token(gst_integration_settings, base_url)
	path = "/enriched/returns/gstr3b?action=RETSUM&gstin={}&ret_period={}".format(gstin, ret_period)
	if gst_integration_settings.is_testing:
		path = "/test/enriched/returns/gstr3b?action=RETSUM&gstin={}&ret_period={}".format(gstin, ret_period)
		
	url = base_url + path
	
	headers = {
		'username':  user_name,
		'state-cd': state_code,
		'otp': otp,
		'Content-Type': content_type,
		'requestid': requestid,
		'gstin': gstin,
		'ret_period': ret_period,
		'Authorization': "Bearer " + access_token,
		
}
	response = requests.request("GET", url, headers=headers)
	
	create_api_log(response, action= "RETSUM")
	
	if response.ok:
		res = response.json()
		if res.get("error_report"):
			frappe.msgprint(json.dumps(res.get("error_report")), title= "Error Report")
		else:
			frappe.msgprint(response.text)
			return response.text
	else:
		frappe.msgprint("Failed")

	
@frappe.whitelist()
def file_gstr3b(ret_period):
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
	requestid = random_string(randint(8,16))
	
	gstin = gst_integration_settings.gstin
	state_code = gstin[:2]
	otp = gst_integration_settings.otp
	
	ret_period = ret_period
		
	if not all([user_name, base_url, content_type, requestid, gstin]):
		frappe.throw("GST Details Missing")
	
	access_token = get_access_token(gst_integration_settings, base_url)
	
	path = r"/enriched/returns/gstr3b?action=RETFILE"
	if gst_integration_settings.is_testing:
		path = r"/test/enriched/returns/gstr3b?action=RETFILE"
		
	url = base_url + path
	
	payload = ret_summary(ret_period)
	
	
	if not payload:
		frappe.throw("No data found for return period {} ".format(ret_period), title= "Data Not Found!")
	
	headers = {
		'username':  user_name,
		'otp': otp,
		'state-cd': state_code,
		'Content-Type': content_type,
		'requestid': requestid,
		'gstin': gstin,
		'ret_period': ret_period,
		'Authorization': "Bearer " + access_token
	}
	
	response = requests.request("POST", url, headers=headers, data= payload)
	
	create_api_log(response, action= "RETFILE")
	
	if response.ok:
		headers.pop('Authorization')
		res = response.json()
		if res:
			if res.get('status') == 200:
				return {
					"msg": res.get('message')
				}
			else:
				frappe.throw(res.get('message'), title= "Failed")
	else:
		res = response.json()
		frappe.throw(res.get('error_description'), title="Error")
