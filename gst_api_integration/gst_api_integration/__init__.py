import frappe

GST_WORKFLOW_STATES = [
	{'workflow_state_name': 'Draft', 'style': 'Warning'},
    {'workflow_state_name': 'Saved', 'style': 'Primary'},
	{'workflow_state_name': 'Verified','style': 'Success'},
]

GST_WORKFLOW_ACTIONS = ['Save', 'Approve', 'Reject']

def create_workflow_state():
	# create new workflow state 
	for wfs in GST_WORKFLOW_STATES:
		if not frappe.db.exists("Workflow State", wfs['workflow_state_name']):
			frappe.get_doc({
				"doctype": "Workflow State",
				'workflow_state_name': wfs['workflow_state_name'],
				'style':wfs['style']
				}).insert()

def create_workflow_actions():
	for wfa in GST_WORKFLOW_ACTIONS:
		if not frappe.db.exists("Workflow Action Master", wfa):
			frappe.get_doc({
				"doctype": "Workflow Action Master",
				'workflow_action_name': wfa,
				}).insert()
		
def create_workflow(document_name):
	create_workflow_state()
	create_workflow_actions()

	if not frappe.db.exists('Workflow', f'{document_name} Workflow'):
		workflow_doc = frappe.get_doc({'doctype': 'Workflow',
				'workflow_name': f'{document_name} Workflow',
				'document_type': document_name,
				'workflow_state_field': 'workflow_state',
				'is_active': 1,
				'send_email_alert':0})
		
		states = [
			{
				'state': 'Draft',
				'doc_status': 0,
				'update_field': 'workflow_state',
				'update_value': '',
				'allow_edit': 'System manager'
			},
			{
				'state': 'Saved',
				'doc_status': 0,
				'update_field': 'workflow_state',
				'update_value': 'Saved',
				'allow_edit': 'System manager'
			},
			{
				'state': 'Verified',
				'doc_status': 1,
				'update_field': 'workflow_state',
				'update_value': 'Verified',
				'allow_edit': 'System manager'
			}]
		for state in states:
			workflow_doc.append('states',state)
		
		transitions = [
			{ 
				'state': 'Draft',
				'action': 'Save',
				'allow_self_approval': 0,
				'next_state': 'Saved',
				'allowed': 'System Manager'
			},
			{ 
				'state': 'Saved',
				'action': 'Approve',
				'allow_self_approval': 0,
				'next_state': 'Saved',
				'allowed': 'System Manager'
			},
			{ 
				'state': 'Saved',
				'action': 'Reject',
				'allow_self_approval': 0,
				'next_state': 'Draft',
				'allowed': 'System Manager'
			}
		]
		
		for transition in transitions: 
			workflow_doc.append('transitions',transition)
			
		workflow_doc.save()
		print(workflow_doc.as_dict())
		
def create_defaults():
	create_workflow('GSTR 1 Report')
	create_workflow('GSTR 3B Report')
