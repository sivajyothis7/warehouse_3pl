import frappe
from frappe.tests.utils import FrappeTestCase

from warehouse_3pl.warehouse_3pl.utils.allocation_engine import allocate_stock

_ITEM_PREFIX = "_Test Alloc Item"
_CLIENT = "_Test Alloc Client"


def _get_company_warehouse():
    """Return a Warehouse that belongs to the first Company."""
    company = frappe.get_all("Company", limit=1)[0].name
    wh = frappe.db.get_value("Warehouse", {"is_group": 0, "company": company}, "name")
    if not wh:
        wh_doc = frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": "Test Allocation Warehouse",
            "company": company,
        })
        wh_doc.insert(ignore_permissions=True)
        wh = wh_doc.name
    return wh


def _ensure_customer():
    if not frappe.db.exists("Customer", _CLIENT):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": _CLIENT,
            "customer_type": "Company",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "is_3pl_client": 1,
            "client_code": "TALC",
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def _ensure_item(item_code):
    """Create item if it doesn't exist, return item_code."""
    if not frappe.db.exists("Item", item_code):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_code,
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "is_stock_item": 1,
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    return item_code


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


class TestAllocationEngine(FrappeTestCase):

    def setUp(self):
        _ensure_customer()

    def tearDown(self):
        frappe.db.rollback()

    # ------------------------------------------------------------------
    # Test 1: FIFO allocation — add 100 stock, allocate 50, verify total=50
    # ------------------------------------------------------------------
    def test_allocate_stock_fifo(self):
        item = _ensure_item(f"{_ITEM_PREFIX} FIFO")
        wh = _get_company_warehouse()
        _add_stock(item, 100, wh)
        try:
            allocations = allocate_stock(
                client=_CLIENT,
                item_code=item,
                qty=50,
            )
            total_allocated = sum(a["qty"] for a in allocations)
            self.assertEqual(total_allocated, 50)
            self.assertGreater(len(allocations), 0)
        finally:
            _cancel_stock_entries_for_item(item)

    # ------------------------------------------------------------------
    # Test 2: Insufficient stock — add 10, request 50, verify partial (<=10)
    # ------------------------------------------------------------------
    def test_allocate_insufficient_stock(self):
        item = _ensure_item(f"{_ITEM_PREFIX} Insuf")
        wh = _get_company_warehouse()
        _add_stock(item, 10, wh)
        try:
            allocations = allocate_stock(
                client=_CLIENT,
                item_code=item,
                qty=50,
            )
            total_allocated = sum(a["qty"] for a in allocations)
            self.assertLessEqual(total_allocated, 10)
        finally:
            _cancel_stock_entries_for_item(item)

    # ------------------------------------------------------------------
    # Test 3: Lot preference for nonexistent lot falls back to FIFO, gets 20
    # ------------------------------------------------------------------
    def test_allocate_with_lot_preference(self):
        item = _ensure_item(f"{_ITEM_PREFIX} Lot")
        wh = _get_company_warehouse()
        _add_stock(item, 100, wh)
        try:
            # Request a lot that doesn't exist — should fall back to normal FIFO
            allocations = allocate_stock(
                client=_CLIENT,
                item_code=item,
                qty=20,
                lot_preference="NONEXISTENT-LOT-XYZ",
            )
            total_allocated = sum(a["qty"] for a in allocations)
            self.assertEqual(total_allocated, 20)
        finally:
            _cancel_stock_entries_for_item(item)

    # ------------------------------------------------------------------
    # Test 4: Nonexistent item — returns empty list
    # ------------------------------------------------------------------
    def test_allocate_no_stock(self):
        allocations = allocate_stock(
            client=_CLIENT,
            item_code="_Test Nonexistent Item XYZ 99999",
            qty=10,
        )
        self.assertEqual(allocations, [])
