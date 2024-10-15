# Copyright (c) 2023, aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class ApiLog(Document):
	pass
		

@frappe.whitelist()
def create_api_log(res, action= None, submit= False):	
	"""Can create API log From response

	Args:
		res (response object): It is used to obtain an API response.
		request_from (str): It is optional for the purposes of the API..
		submit (bool, True): If true, submit the log. False is the default value.	
	"""
	if not res: return
	
	log_doc = frappe.new_doc("Api Log")
	log_doc.action = action
	log_doc.url = res.request.url
	log_doc.method = res.request.method
	log_doc.header = json.dumps(dict(res.request.headers),indent=4, sort_keys=True)
	log_doc.payload =res.request.body
	log_doc.response = json.dumps(res.json(),indent=4, sort_keys=True)
	log_doc.status_code = res.status_code
	log_doc.insert()
	
	if submit:log_doc.submit()
	
	frappe.db.commit()
