# Copyright (c) 2023, aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import random_string
from random import randint

class GSTIntegrationSettings(Document):
	def before_save(self):
		self.state_code = self.gstin[:2] if self.gstin else ""
		
	
		 
		
