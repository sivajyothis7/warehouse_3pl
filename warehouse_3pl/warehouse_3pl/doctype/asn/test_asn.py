import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


def _setup_fixtures():
    """Create shared test fixtures (idempotent)."""
    if not frappe.db.exists("Customer", "_Test ASN Client"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "_Test ASN Client",
            "customer_type": "Company",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "is_3pl_client": 1,
            "client_code": "TASN",
        }).insert(ignore_permissions=True)

    if not frappe.db.exists("Customer", "_Test Non3PL Client"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "_Test Non3PL Client",
            "customer_type": "Company",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "is_3pl_client": 0,
        }).insert(ignore_permissions=True)

    if not frappe.db.exists("Item", "_Test ASN Item"):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": "_Test ASN Item",
            "item_name": "_Test ASN Item",
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "is_stock_item": 1,
        }).insert(ignore_permissions=True)


def _make_asn(client="_Test ASN Client", expected_qty=10.0):
    """Build an unsaved ASN document."""
    return frappe.get_doc({
        "doctype": "ASN",
        "naming_series": "ASN-.YYYY.-.#####",
        "client": client,
        "expected_date": frappe.utils.today(),
        "items": [
            {
                "item_code": "_Test ASN Item",
                "expected_qty": expected_qty,
                "uom": "Nos",
            }
        ],
    })


class TestASN(FrappeTestCase):

    def setUp(self):
        _setup_fixtures()
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    # ------------------------------------------------------------------
    # Test 1: Submit ASN -> status becomes Confirmed
    # ------------------------------------------------------------------
    def test_submit_sets_status_confirmed(self):
        doc = _make_asn()
        doc.insert(ignore_permissions=True)
        doc.submit()
        self.assertEqual(doc.status, "Confirmed")

    # ------------------------------------------------------------------
    # Test 2: Cancel ASN -> status becomes Cancelled
    # ------------------------------------------------------------------
    def test_cancel_sets_status_cancelled(self):
        doc = _make_asn()
        doc.insert(ignore_permissions=True)
        doc.submit()
        doc.cancel()
        self.assertEqual(doc.status, "Cancelled")

    # ------------------------------------------------------------------
    # Test 3: Non-3PL client is rejected on insert
    # ------------------------------------------------------------------
    def test_non_3pl_client_rejected(self):
        doc = _make_asn(client="_Test Non3PL Client")
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 4: Zero qty line is rejected on insert
    # ------------------------------------------------------------------
    def test_zero_qty_line_rejected(self):
        doc = _make_asn(expected_qty=0)
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)
