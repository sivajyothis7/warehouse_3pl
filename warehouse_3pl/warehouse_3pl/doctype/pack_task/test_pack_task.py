import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


_CLIENT = "_Test Pack Client"
_ITEM = "_Test Pack Item"


def _setup_fixtures():
    """Create shared test fixtures (idempotent)."""
    if not frappe.db.exists("Customer", _CLIENT):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": _CLIENT,
            "customer_type": "Company",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "is_3pl_client": 1,
            "client_code": "TPCK",
        }).insert(ignore_permissions=True)

    if not frappe.db.exists("Item", _ITEM):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": _ITEM,
            "item_name": _ITEM,
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "is_stock_item": 1,
        }).insert(ignore_permissions=True)

    frappe.db.commit()


def _get_company_warehouse():
    company = frappe.get_all("Company", limit=1)[0].name
    wh = frappe.db.get_value("Warehouse", {"is_group": 0, "company": company}, "name")
    return wh


def _add_stock(item_code, qty, warehouse):
    company = frappe.db.get_value("Warehouse", warehouse, "company")
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company": company,
        "items": [
            {
                "item_code": item_code,
                "qty": qty,
                "t_warehouse": warehouse,
                "allow_zero_valuation_rate": 1,
            }
        ],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    frappe.db.commit()
    return se


def _make_client_order(client=_CLIENT, item=_ITEM, qty=10.0):
    """Create and submit a Client Order."""
    doc = frappe.get_doc({
        "doctype": "Client Order",
        "naming_series": "CO-.YYYY.-.#####",
        "client": client,
        "order_date": frappe.utils.today(),
        "items": [{"item_code": item, "qty": qty, "uom": "Nos"}],
    })
    doc.insert(ignore_permissions=True)
    doc.submit()
    frappe.db.commit()
    return doc


def _make_pack_task(client_order_name, client=_CLIENT, item=_ITEM, qty=10.0):
    """Create a Pack Task linked to a Client Order."""
    doc = frappe.get_doc({
        "doctype": "Pack Task",
        "naming_series": "PACK-.YYYY.-.#####",
        "client_order": client_order_name,
        "client": client,
        "status": "Pending",
        "items": [{"item_code": item, "qty": qty}],
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


class TestPackTask(FrappeTestCase):

    def setUp(self):
        _setup_fixtures()

    def tearDown(self):
        frappe.db.rollback()

    # Test 1: Create pack task -> status Pending
    def test_create_pack_task_status_pending(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pack = _make_pack_task(order.name)
        self.assertEqual(pack.status, "Pending")

    # Test 2: Complete -> creates Delivery Note
    def test_complete_creates_delivery_note(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pack = _make_pack_task(order.name)
        pack.complete()
        pack.reload()
        self.assertEqual(pack.status, "Complete")
        self.assertTrue(pack.delivery_note)
        dn = frappe.get_doc("Delivery Note", pack.delivery_note)
        self.assertEqual(dn.docstatus, 1)

    # Test 3: Complete -> updates order status to Shipped
    def test_complete_updates_order_status_to_shipped(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pack = _make_pack_task(order.name)
        pack.complete()
        order.reload()
        self.assertEqual(order.status, "Shipped")

    # Test 4: Double complete -> raises error
    def test_double_complete_raises_error(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pack = _make_pack_task(order.name)
        pack.complete()
        with self.assertRaises(ValidationError):
            pack.complete()
