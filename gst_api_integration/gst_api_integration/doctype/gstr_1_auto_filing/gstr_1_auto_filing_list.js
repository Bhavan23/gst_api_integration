frappe.listview_settings["GSTR-1 Auto Filing"] = {
	get_indicator: function (doc) {
		if (doc.status == 'Failed') {
			return [(doc.status), "red"];
		}
		else if (doc.status == 'Succesfully Filed') {
			return [(doc.status), "green"];
		}
	}
}
