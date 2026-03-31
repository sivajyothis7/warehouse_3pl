import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


def _get_test_customer():
    """Create or return _Test RCV Client with is_3pl_client=1."""
    if not frappe.db.exists("Customer", "_Test RCV Client"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "_Test RCV Client",
            "customer_type": "Company",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "is_3pl_client": 1,
            "client_code": "TRCV",
        }).insert(ignore_permissions=True)
    return "_Test RCV Client"


def _get_test_item():
    """Create or return _Test RCV Item (stock item)."""
    if not frappe.db.exists("Item", "_Test RCV Item"):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": "_Test RCV Item",
            "item_name": "_Test RCV Item",
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "is_stock_item": 1,
        }).insert(ignore_permissions=True)
    return "_Test RCV Item"


def _get_staging_warehouse():
    """Create or return _Test Staging warehouse."""
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        company = frappe.get_all("Company", limit=1)[0].name
    abbr = frappe.db.get_value("Company", company, "abbr")
    full_name = f"_Test Staging - {abbr}"

    if not frappe.db.exists("Warehouse", full_name):
        frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": "_Test Staging",
            "company": company,
        }).insert(ignore_permissions=True)
    return full_name


def _make_receiving(client=None, item_code=None, staging=None, asn=None, received_qty=10.0):
    """Build an unsaved Receiving document."""
    client = client or _get_test_customer()
    item_code = item_code or _get_test_item()
    staging = staging or _get_staging_warehouse()

    doc = frappe.get_doc({
        "doctype": "Receiving",
        "naming_series": "RCV-.YYYY.-.#####",
        "client": client,
        "receiving_date": frappe.utils.today(),
        "staging_location": staging,
        "asn": asn,
        "items": [
            {
                "item_code": item_code,
                "received_qty": received_qty,
                "condition": "Good",
            }
        ],
    })
    return doc


class TestReceiving(FrappeTestCase):

    def setUp(self):
        _get_test_customer()
        _get_test_item()
        _get_staging_warehouse()
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    # ------------------------------------------------------------------
    # Test 1: Submit Receiving -> status Complete, docstatus 1
    # ------------------------------------------------------------------
    def test_create_and_submit_receiving(self):
        doc = _make_receiving()
        doc.insert(ignore_permissions=True)
        doc.submit()
        doc.reload()
        self.assertEqual(doc.docstatus, 1)
        self.assertEqual(doc.status, "Complete")

    # ------------------------------------------------------------------
    # Test 2: Stock Entry created on submit
    # ------------------------------------------------------------------
    def test_stock_entry_created_on_submit(self):
        doc = _make_receiving()
        doc.insert(ignore_permissions=True)
        doc.submit()
        doc.reload()

        self.assertTrue(doc.stock_entry)
        se = frappe.get_doc("Stock Entry", doc.stock_entry)
        self.assertEqual(se.stock_entry_type, "Material Receipt")
        self.assertEqual(se.docstatus, 1)
        for item in se.items:
            self.assertTrue(
                item.allow_zero_valuation_rate or item.basic_rate == 0,
                "Stock Entry item should allow zero valuation rate"
            )

    # ------------------------------------------------------------------
    # Test 3: Putaway Tasks created on submit
    # ------------------------------------------------------------------
    def test_putaway_tasks_created_on_submit(self):
        doc = _make_receiving()
        doc.insert(ignore_permissions=True)
        doc.submit()

        tasks = frappe.get_all(
            "Putaway Task",
            filters={"receiving_ref": doc.name},
            fields=["name", "status", "receiving_ref"],
        )
        self.assertGreaterEqual(len(tasks), 1)
        self.assertEqual(tasks[0].receiving_ref, doc.name)
        self.assertEqual(tasks[0].status, "Pending")

    # ------------------------------------------------------------------
    # Test 4: ASN status updated to Received on submit
    # ------------------------------------------------------------------
    def test_asn_status_updated_on_submit(self):
        # Create and submit an ASN first
        asn = frappe.get_doc({
            "doctype": "ASN",
            "naming_series": "ASN-.YYYY.-.#####",
            "client": _get_test_customer(),
            "expected_date": frappe.utils.today(),
            "items": [
                {
                    "item_code": _get_test_item(),
                    "expected_qty": 10,
                    "uom": "Nos",
                }
            ],
        })
        asn.insert(ignore_permissions=True)
        asn.submit()
        self.assertEqual(asn.status, "Confirmed")

        # Create and submit Receiving linked to the ASN
        doc = _make_receiving(asn=asn.name)
        doc.insert(ignore_permissions=True)
        doc.submit()

        asn.reload()
        self.assertEqual(asn.status, "Received")

    # ------------------------------------------------------------------
    # Test 5: Cancel Receiving cancels Stock Entry
    # ------------------------------------------------------------------
    def test_cancel_receiving_cancels_stock_entry(self):
        doc = _make_receiving()
        doc.insert(ignore_permissions=True)
        doc.submit()
        doc.reload()

        se_name = doc.stock_entry
        self.assertTrue(se_name)

        doc.cancel()
        se = frappe.get_doc("Stock Entry", se_name)
        self.assertEqual(se.docstatus, 2)

    # ------------------------------------------------------------------
    # Test 6: Non-3PL client is rejected
    # ------------------------------------------------------------------
    def test_non_3pl_client_rejected(self):
        # Create a non-3PL customer
        non_3pl = "_Test Non3PL RCV Client"
        if not frappe.db.exists("Customer", non_3pl):
            frappe.get_doc({
                "doctype": "Customer",
                "customer_name": non_3pl,
                "customer_type": "Company",
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
                "is_3pl_client": 0,
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        doc = _make_receiving(client=non_3pl)
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)
