import json

import frappe
from frappe import _, msgprint
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, get_link_to_form, getdate, new_line_sep, nowdate
from six import string_types
from erpnext.stock.doctype.item.item import get_item_defaults




def set_missing_values(source, target_doc):
	if target_doc.doctype == "Purchase Order" and getdate(target_doc.schedule_date) < getdate(
		nowdate()
	):
		target_doc.schedule_date = None
	target_doc.run_method("set_missing_values")
	target_doc.run_method("calculate_taxes_and_totals")


def update_item(obj, target, source_parent):
	target.conversion_factor = obj.conversion_factor
	target.qty = flt(flt(obj.stock_qty) - flt(obj.ordered_qty)) / target.conversion_factor
	target.stock_qty = target.qty * target.conversion_factor
	if getdate(target.schedule_date) < getdate(nowdate()):
		target.schedule_date = None

@frappe.whitelist()
def make_multiple_purchase_order(source_name, target_doc=None, args=None):
	
	result_doclist=[]
	doc = frappe.get_doc("Material Request", source_name)
	item_list = []
	for d in doc.items:
		item_list.append(d.item_code)
	supplier_list=frappe.db.sql(
		"""select DISTINCT(default_supplier)
		from `tabItem Default`
		where parent in ({0}) and
		company = '{1}' """.format(", ".join(["%s"] * len(item_list)),doc.company),tuple(item_list),as_list=1)
	for supplier in supplier_list:

		if args is None:
			args = {}
		if isinstance(args, string_types):
			args = json.loads(args)

		def postprocess(source, target_doc):
			# items only for given default supplier
			supplier_items = []
			idx=1
			for d in target_doc.get('items'):
				default_supplier = get_item_defaults(d.item_code, target_doc.company).get("default_supplier") 
				if supplier[0] == default_supplier :
					d.idx=idx
					idx=idx+1
					supplier_items.append(d)
					
			target_doc.items = supplier_items

			set_missing_values(source, target_doc)

		def select_item(d):
			# filtered_items = args.get("filtered_children", [])
			child_filter =  True

			return d.ordered_qty < d.stock_qty and child_filter

		doclist = get_mapped_doc(
			"Material Request",
			source_name,
			{
				"Material Request": {
					"doctype": "Purchase Order",
					"validation": {"docstatus": ["=", 1], "material_request_type": ["=", "Purchase"]},
				},
				"Material Request Item": {
					"doctype": "Purchase Order Item",
					"field_map": [
						["name", "material_request_item"],
						["parent", "material_request"],
						["uom", "stock_uom"],
						["uom", "uom"],
						["sales_order", "sales_order"],
						["sales_order_item", "sales_order_item"],
					],
					"postprocess": update_item,
					"condition": select_item,
				},
			},
			target_doc,
			postprocess,
		)
		if doclist.supplier:
			doclist.save(ignore_permissions=True)
		result_doclist.append(doclist)
	return result_doclist