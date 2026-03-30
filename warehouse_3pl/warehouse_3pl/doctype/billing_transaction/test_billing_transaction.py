import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from warehouse_3pl.warehouse_3pl.utils.billing import create_billing_transaction


def get_or_create_test_client():
    """Return existing test client or create a new one."""
    if frappe.db.exists("Customer", "_Test BT Client"):
        return frappe.get_doc("Customer", "_Test BT Client")

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": "_Test BT Client",
        "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups",
        "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories",
        "is_3pl_client": 1,
    })
    customer.insert(ignore_permissions=True)
    return customer


def make_active_rate_card(client):
    """Create an active Rate Card with Receiving, Storage, and Picking lines."""
    doc = frappe.get_doc({
        "doctype": "Rate Card",
        "client": client,
        "effective_from": today(),
        "status": "Active",
        "rate_lines": [
            {"activity_type": "Receiving", "uom": "Per Pallet", "rate": 12.50, "minimum_charge": 0},
            {"activity_type": "Storage", "uom": "Per Pallet", "rate": 8.00, "minimum_charge": 500},
            {"activity_type": "Picking", "uom": "Per Unit", "rate": 0.50, "minimum_charge": 0},
        ],
    })
    doc.insert(ignore_permissions=True)
    return doc


class TestBillingTransaction(FrappeTestCase):

    def setUp(self):
        self.client = get_or_create_test_client()
        self.rate_card = make_active_rate_card(self.client.name)

    def tearDown(self):
        frappe.db.rollback()

    # ------------------------------------------------------------------
    # Test 1: Create billing transaction — verify amount and billing_period
    # ------------------------------------------------------------------
    def test_create_billing_transaction(self):
        bt = frappe.get_doc({
            "doctype": "Billing Transaction",
            "client": self.client.name,
            "activity_type": "Receiving",
            "qty": 10,
            "uom": "Per Pallet",
            "rate": 12.50,
            "transaction_date": today(),
            "source_doctype": "Inbound Shipment",
            "source_name": "TEST-001",
        })
        bt.insert(ignore_permissions=True)

        saved = frappe.get_doc("Billing Transaction", bt.name)
        self.assertEqual(saved.amount, 125.0)
        self.assertEqual(saved.billing_period, today()[:7])

    # ------------------------------------------------------------------
    # Test 2: Auto-calculate amount (rate * qty)
    # ------------------------------------------------------------------
    def test_auto_calculate_amount(self):
        bt = frappe.get_doc({
            "doctype": "Billing Transaction",
            "client": self.client.name,
            "activity_type": "Picking",
            "qty": 200,
            "uom": "Per Unit",
            "rate": 0.50,
            "transaction_date": today(),
            "source_doctype": "Pick List",
            "source_name": "TEST-002",
        })
        bt.insert(ignore_permissions=True)

        self.assertEqual(bt.amount, 100.0)

    # ------------------------------------------------------------------
    # Test 3: Billing helper creates transaction using rate card lookup
    # ------------------------------------------------------------------
    def test_helper_creates_transaction(self):
        bt_name = create_billing_transaction(
            client=self.client.name,
            activity_type="Receiving",
            qty=5,
            source_doctype="Inbound Shipment",
            source_name="TEST-003",
            uom="Per Pallet",
        )

        self.assertIsNotNone(bt_name)
        bt = frappe.get_doc("Billing Transaction", bt_name)
        self.assertEqual(bt.client, self.client.name)
        self.assertEqual(bt.activity_type, "Receiving")
        self.assertEqual(bt.qty, 5)
        self.assertEqual(bt.rate, 12.50)
        self.assertEqual(bt.amount, 62.50)

    # ------------------------------------------------------------------
    # Test 4: Billing helper returns None when no rate configured
    # ------------------------------------------------------------------
    def test_helper_returns_none_when_no_rate(self):
        bt_name = create_billing_transaction(
            client=self.client.name,
            activity_type="VAS-Kitting",
            qty=10,
            source_doctype="Work Order",
            source_name="TEST-004",
            uom="Per Unit",
        )

        self.assertIsNone(bt_name)
