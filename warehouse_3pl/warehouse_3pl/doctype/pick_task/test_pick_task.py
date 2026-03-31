import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


_CLIENT = "_Test Pick Client"
_ITEM = "_Test Pick Item"


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
            "client_code": "TPIK",
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


def _make_pick_task(client_order_name, client=_CLIENT, item=_ITEM, qty=10.0, warehouse=None):
    if not warehouse:
        warehouse = _get_company_warehouse()
    doc = frappe.get_doc({
        "doctype": "Pick Task",
        "naming_series": "PICK-.YYYY.-.#####",
        "client_order": client_order_name,
        "client": client,
        "status": "Pending",
        "items": [{
            "item_code": item,
            "qty": qty,
            "from_location": warehouse,
            "status": "Pending",
        }],
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


class TestPickTask(FrappeTestCase):

    def setUp(self):
        _setup_fixtures()

    def tearDown(self):
        frappe.db.rollback()

    # Test 1: Create -> status Pending
    def test_create_pick_task_status_pending(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pick = _make_pick_task(order.name, warehouse=wh)
        self.assertEqual(pick.status, "Pending")

    # Test 2: Start -> status In Progress, started_at set
    def test_start_sets_in_progress(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pick = _make_pick_task(order.name, warehouse=wh)
        pick.start()
        pick.reload()
        self.assertEqual(pick.status, "In Progress")
        self.assertIsNotNone(pick.started_at)

    # Test 3: Complete -> creates Pack Task, status Complete
    def test_complete_creates_pack_task(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pick = _make_pick_task(order.name, warehouse=wh)
        pick.complete()
        pick.reload()
        self.assertEqual(pick.status, "Complete")
        pack_tasks = frappe.get_all("Pack Task", filters={"pick_task": pick.name})
        self.assertTrue(len(pack_tasks) > 0)

    # Test 4: Complete -> updates order status to Packing
    def test_complete_updates_order_status_to_packing(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        pick = _make_pick_task(order.name, warehouse=wh)
        pick.complete()
        order.reload()
        self.assertEqual(order.status, "Packing")
