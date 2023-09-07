# Copyright (c) 2023, aerele and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe.utils.change_log import get_versions
if get_versions().get("erpnext"):
	if int(get_versions().get("erpnext").get("version").split(".")[0]) < 14:
		from erpnext.regional.report.gstr_1.gstr_1 import  get_json, execute
	else:
		from india_compliance.gst_india.report.gstr_1.gstr_1 import get_json, execute
		
import json
import requests
from frappe.utils import getdate

class GSTR1AutoFiling(Document):
	field_map = {
			"B2B Invoices - 4A, 4B, 4C, 6B, 6C" : "B2B",
			"B2C(Large) Invoices - 5A, 5B": "B2C Large" ,
			"B2C(Small) Invoices - 7" : "B2C Small",
			"Credit/Debit Notes (Registered) - 9B": "CDNR-REG",
			"Credit/Debit Notes (Unregistered) - 9B": "CDNR-UNREG",
			"Export Invoice - 6A" : "EXPORT",
			"Tax Liability (Advances Received) - 11A(1), 11A(2)": "Advances",
			"NIL RATED/EXEMPTED Invoices": "NIL Rated"
		}
	def autoname(self):
		self.name =  "GSTR1-"+ self.field_map.get(self.type_of_business)+"-"+self.from_date+"-"+self.to_date
		
	def before_save(self):
		#validate existing document 
		if self.from_date and self.is_new():
			if frappe.db.sql("select name from `tabGSTR-1 Auto Filing` where to_date BETWEEN '{0}' AND '{1}' AND  docstatus < 2 AND type_of_business = '{2}'".format(self.from_date, self.to_date, self.type_of_business ), debug= True):
				frappe.throw("Already document exists for given date <b>{}</b>".format(self.from_date), title="Document Already Exists")
				
		if self.to_date and self.from_date:
			if getdate(self.to_date) <  getdate(self.from_date):
				frappe.throw("To date cannot be before the from date",  title="Invalid Date")
				
		filters = {'company': self.company, 'company_address': self.company_address, 'company_gstin': self.company_gstin, 'from_date': self.from_date, 'to_date': self.to_date, 'type_of_business': self.field_map.get(self.type_of_business)}
		
		filters = {filter: filters.get(filter) for filter in filters if filters.get(filter)}
		
		columns, datas = execute(filters=filters)
		
		new_datas = []
		
		if not datas:
			frappe.throw("Data not found for the given period!", "No Data")
			
		if isinstance(datas[0],list) or isinstance(datas[0],tuple):
			for data in datas:
				d = {column.get('fieldname') : data[i]  for i, column in enumerate(columns) }
				new_datas.append(d)
			else:
				new_datas.append({})
		else:
			new_datas = datas
		try:
			json_data = get_json(data= json.dumps(new_datas),	report_name= 'GSTR-1', filters= json.dumps(filters))
		except KeyError as e:
			frappe.throw(str(e).replace("'", '').replace("_", ' ').title(), title="Missing Value")
		except Exception as e:
			frappe.throw(str(e), "Error")
			
		if frappe.get_single('GST Integration Settings').is_testing:
			self.json_file = "{}"
			return
		
		self.json_file = json.dumps(json_data.get("data"))
		
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
	
	if response.ok:
		return response.json().get("access_token")
	else:
		frappe.throw(response.json().get("error_description"), title= "Failed")
		
#save gstr1
@frappe.whitelist()
def save_gstr1(json_file, gstin = None, to_date = None):
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
	otp = gst_integration_settings.otp
	requestid = gst_integration_settings.requestid
	
	if gstin:
		state_code = gstin[:2] 
	else:
		gstin = gst_integration_settings.gstin
		state_code = gstin[:2]
	
	ret_period = gst_integration_settings.ret_period
	if to_date:
		ret_period = getdate(to_date).strftime("%m%Y")
		
	if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
		frappe.throw("GST Details Missing")
	
	access_token = get_access_token(gst_integration_settings, base_url)
			
	path = "/enriched/returns/gstr1?action=RETSAVE"
	if gst_integration_settings.is_testing:
		path = "/test/enriched/returns/gstr1?action=RETSAVE"
		
	url = base_url + path
	
	payload = json.loads(json_file)
	
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
	# import pdb; pdb.set_trace()
	
	if response.ok:
		res = response.json()
		headers.pop('Authorization')
		headers.pop('otp')
		if res:
			if res.get('status') == 200:
				return {'headers': headers, 'res' : json.dumps(res), 'status': 'Saved Successfully', 'msg': res.get('message')}
			else:
				return {'headers': headers, 'res' : json.dumps(res), 'status': 'Failed', 'msg': res.get('message')}
	else:
		res = response.json()
		return {'headers': headers, 'res' : json.dumps(res), 'status': 'Failed', 'msg':res.get('message')}
	
@frappe.whitelist()
def gstr1_status(doc_name):
	# import pdb; pdb.set_trace()
	doc = frappe.get_doc("GSTR-1 Auto Filing", doc_name)
	
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
		
	# import pdb; pdb.set_trace()	
	
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
	# import pdb; pdb.set_trace()	
	
	if response.ok:
		# import pdb; pdb.set_trace()
		res = response.json()
		if res.get("error_report"):
			frappe.msgprint(json.dumps(res.get("error_report")), title= "Error Report")
		else:
			frappe.msgprint("No Error Report")
	else:
		frappe.msgprint("Failed")
		
@frappe.whitelist()
def proceed_to_file(doc_name):
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	doc = frappe.get_doc("GSTR-1 Auto Filing", doc_name)
	
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
	path = r"/enriched/returns/gstrptf?action=RETNEWPTF"
	if gst_integration_settings.is_testing:
		path = r"/test/enriched/returns/gstrptf?action=RETNEWPTF"
		
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
		'rtn_typ': 'GSTR1',
		'userrole': 'GSTR1'
		
}
	response = requests.request("POST", url, headers=headers, data= payload)
	
	# import pdb; pdb.set_trace()
	
	if response.ok:
		headers.pop('Authorization')
		headers.pop('otp')
		res = response.json()
		if res:
			if res.get('status') == 200:
				return {
					"headers" : headers,
					"payload" : payload,
					"res" : json.dumps(res),
					"status" : "Proceeded",
					"msg": res.get('message')
				}
			else:
				frappe.throw(res.get('message'), title= "Failed")
	else:
		res = response.json()
		frappe.throw(res.get('error_description'), title="Error")
	
@frappe.whitelist()
def send_otp(doc_name= None):
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	doc = frappe.get_doc("GSTR-1 Auto Filing", doc_name) if doc_name else None
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
	otp = gst_integration_settings.otp
	saved_data = json.loads(doc.saved_headers) if doc else None
	if saved_data:
		requestid = saved_data.get('requestid')
	else:
		requestid = gst_integration_settings.requestid
	
	gstin = doc.company_gstin if doc else None
	
	if gstin:
		state_code = gstin[:2] 
	else:
		gstin = gst_integration_settings.gstin
		state_code = gstin[:2]
	
	ret_period = gst_integration_settings.ret_period
	if doc and doc.to_date:
		ret_period = getdate(doc.to_date).strftime("%m%Y")
	
	pan = gst_integration_settings.pan
	
	print([user_name, base_url, content_type, requestid, gstin, ret_period, pan])
	if not all([user_name, base_url, content_type, requestid, gstin, ret_period, pan]):
		frappe.throw("GST Details Missing")
	
	access_token = get_access_token(gst_integration_settings, base_url)
	path = r"/test/enriched/authenticate"
	if gst_integration_settings.is_testing:
		path = r"/test/enriched/authenticate"
		
	url = base_url + path
	
	params = {
		"action":"EVCOTP",
		"gstin":gstin,
		"pan": pan,
		"form_type":"R1"
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
		'pan': pan,
		'st': 'EVC'
}
	response = requests.request("POST", url, params=params, headers=headers)
	
	if response.ok:
		return 1
	else:
		res = response.json()
		frappe.throw(res.get('error_description'), title="Error")
	
@frappe.whitelist()
def file_gstr1(otp, doc_name):
	gst_integration_settings = frappe.get_single('GST Integration Settings')
	doc = frappe.get_doc("GSTR-1 Auto Filing", doc_name)
	
	#GST integration Details
	user_name = gst_integration_settings.user_name
	base_url = gst_integration_settings.base_url
	content_type = gst_integration_settings.content_type
	
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
	
	pan = gst_integration_settings.pan
	
	print([user_name, base_url, content_type, requestid, gstin, ret_period, pan])
	if not all([user_name, base_url, content_type, requestid, gstin, ret_period, pan]):
		frappe.throw("GST Details Missing")
	
	access_token = get_access_token(gst_integration_settings, base_url)
	path = r"/enriched/returns/gstr1?action=RETFILE"
	if gst_integration_settings.is_testing:
		path = r"/test/enriched/returns/gstr1?action=RETFILE"
		
	url = base_url + path
	
	headers = {
		'username':  user_name,
		'state-cd': state_code,
		'Content-Type': content_type,
		'requestid': requestid,
		'gstin': gstin,
		'ret_period': ret_period,
		'Authorization': "Bearer " + access_token,
		'pan': pan,
		'st': 'EVC',
		'evcotp': otp
		
		
	}
	
	# import pdb; pdb.set_trace()
	
	response = requests.request("POST", url, headers=headers)
	
	# import pdb; pdb.set_trace()
	
	if response.ok:
		headers.pop('Authorization')
		headers.pop('evcotp')
		res = response.json()
		if res:
			if res.get('status') == 200:
				return {
					"headers" : headers,
					"res" : json.dumps(res),
					"status" : "Succesfully Filed",
					"reference_id" : res.get('result').get("reference_id") if res.get('result') else "",
					"msg": res.get('message')
				}
			else:
				frappe.throw(res.get('message'), title= "Failed")
	else:
		res = response.json()
		frappe.throw(res.get('error_description'), title="Error")
	
	
	
