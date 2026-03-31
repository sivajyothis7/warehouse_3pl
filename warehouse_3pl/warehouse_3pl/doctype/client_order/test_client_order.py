import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


_CLIENT = "_Test CO Client"
_NON3PL = "_Test CO Non3PL"
_ITEM = "_Test CO Item"


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
            "client_code": "TCO1",
        }).insert(ignore_permissions=True)

    if not frappe.db.exists("Customer", _NON3PL):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": _NON3PL,
            "customer_type": "Company",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "is_3pl_client": 0,
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
    """Return a Warehouse belonging to the first Company."""
    company = frappe.get_all("Company", limit=1)[0].name
    wh = frappe.db.get_value("Warehouse", {"is_group": 0, "company": company}, "name")
    return wh


def _add_stock(item_code, qty, warehouse):
    """Add stock via Stock Entry Material Receipt."""
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


def _cancel_stock_entries_for_item(item_code):
    """Cancel all submitted Stock Entries that contain the given item."""
    sle_entries = frappe.db.sql("""
        SELECT DISTINCT voucher_no FROM `tabStock Ledger Entry`
        WHERE item_code = %s AND voucher_type = 'Stock Entry' AND is_cancelled = 0
    """, item_code, as_list=True)
    for (se_name,) in sle_entries:
        try:
            se_doc = frappe.get_doc("Stock Entry", se_name)
            if se_doc.docstatus == 1:
                se_doc.cancel()
                frappe.db.commit()
        except Exception:
            pass


def _make_order(client=_CLIENT, qty=10.0, item=_ITEM):
    """Build an unsaved Client Order document."""
    return frappe.get_doc({
        "doctype": "Client Order",
        "naming_series": "CO-.YYYY.-.#####",
        "client": client,
        "order_date": frappe.utils.today(),
        "items": [
            {
                "item_code": item,
                "qty": qty,
                "uom": "Nos",
            }
        ],
    })


class TestClientOrder(FrappeTestCase):

    def setUp(self):
        _setup_fixtures()

    def tearDown(self):
        frappe.db.rollback()

    # ------------------------------------------------------------------
    # Test 1: Create + submit → status in [Confirmed, Allocated]
    # ------------------------------------------------------------------
    def test_create_and_submit_sets_status(self):
        doc = _make_order()
        doc.insert(ignore_permissions=True)
        doc.submit()
        self.assertIn(doc.status, ["Confirmed", "Allocated"])

    # ------------------------------------------------------------------
    # Test 2: Allocation with stock → status "Allocated", allocated_qty = qty
    # ------------------------------------------------------------------
    def test_submit_with_stock_allocates_fully(self):
        item = f"{_ITEM} Alloc"
        if not frappe.db.exists("Item", item):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": item,
                "item_name": item,
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "is_stock_item": 1,
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        wh = _get_company_warehouse()
        se = _add_stock(item, 100, wh)
        try:
            doc = frappe.get_doc({
                "doctype": "Client Order",
                "naming_series": "CO-.YYYY.-.#####",
                "client": _CLIENT,
                "order_date": frappe.utils.today(),
                "items": [{"item_code": item, "qty": 10.0, "uom": "Nos"}],
            })
            doc.insert(ignore_permissions=True)
            doc.submit()
            doc.reload()
            self.assertEqual(doc.status, "Allocated")
            self.assertEqual(doc.items[0].allocated_qty, 10.0)
        finally:
            _cancel_stock_entries_for_item(item)

    # ------------------------------------------------------------------
    # Test 3: Partial allocation → status "Confirmed"
    # ------------------------------------------------------------------
    def test_partial_allocation_sets_status_confirmed(self):
        item = f"{_ITEM} Partial"
        if not frappe.db.exists("Item", item):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": item,
                "item_name": item,
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "is_stock_item": 1,
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        wh = _get_company_warehouse()
        se = _add_stock(item, 5, wh)
        try:
            doc = frappe.get_doc({
                "doctype": "Client Order",
                "naming_series": "CO-.YYYY.-.#####",
                "client": _CLIENT,
                "order_date": frappe.utils.today(),
                "items": [{"item_code": item, "qty": 50.0, "uom": "Nos"}],
            })
            doc.insert(ignore_permissions=True)
            doc.submit()
            doc.reload()
            self.assertEqual(doc.status, "Confirmed")
            self.assertLess(doc.items[0].allocated_qty, doc.items[0].qty)
        finally:
            _cancel_stock_entries_for_item(item)

    # ------------------------------------------------------------------
    # Test 4: Non-3PL client is rejected on insert
    # ------------------------------------------------------------------
    def test_non_3pl_client_rejected(self):
        doc = _make_order(client=_NON3PL)
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 5: Zero qty line is rejected on insert
    # ------------------------------------------------------------------
    def test_zero_qty_line_rejected(self):
        doc = _make_order(qty=0)
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)
