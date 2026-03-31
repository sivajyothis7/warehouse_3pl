import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


_CLIENT = "_Test Wave Client"
_ITEM = "_Test Wave Item"


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
            "client_code": "TWAV",
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


def _make_wave(client_order_name):
    doc = frappe.get_doc({
        "doctype": "Wave",
        "naming_series": "WAV-.YYYY.-.#####",
        "wave_date": frappe.utils.today(),
        "picking_strategy": "Single Order",
        "status": "Planning",
        "orders": [{"client_order": client_order_name}],
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


class TestWave(FrappeTestCase):

    def setUp(self):
        _setup_fixtures()

    def tearDown(self):
        frappe.db.rollback()

    # Test 1: Create wave -> status Planning, total_orders=1
    def test_create_wave_status_planning(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        wave = _make_wave(order.name)
        self.assertEqual(wave.status, "Planning")
        self.assertEqual(wave.total_orders, 1)

    # Test 2: Release -> creates Pick Tasks, status Released
    def test_release_creates_pick_tasks(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        wave = _make_wave(order.name)
        wave.release()
        wave.reload()
        self.assertEqual(wave.status, "Released")
        pick_tasks = frappe.get_all("Pick Task", filters={"wave": wave.name})
        self.assertTrue(len(pick_tasks) > 0)

    # Test 3: Release -> updates order status to Picking
    def test_release_updates_order_status_to_picking(self):
        wh = _get_company_warehouse()
        _add_stock(_ITEM, 100, wh)
        order = _make_client_order()
        wave = _make_wave(order.name)
        wave.release()
        order.reload()
        self.assertEqual(order.status, "Picking")

    # Test 4: Non-submitted order -> rejected on insert
    def test_non_submitted_order_rejected(self):
        # Create a draft (non-submitted) order
        doc = frappe.get_doc({
            "doctype": "Client Order",
            "naming_series": "CO-.YYYY.-.#####",
            "client": _CLIENT,
            "order_date": frappe.utils.today(),
            "items": [{"item_code": _ITEM, "qty": 10.0, "uom": "Nos"}],
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        # Draft order (docstatus=0) should be rejected
        with self.assertRaises(ValidationError):
            _make_wave(doc.name)
