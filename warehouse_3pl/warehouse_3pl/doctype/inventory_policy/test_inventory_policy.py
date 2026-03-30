import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


def get_or_create_test_client():
    """Return existing test client or create a new one."""
    if frappe.db.exists("Customer", "_Test 3PL Client"):
        return frappe.get_doc("Customer", "_Test 3PL Client")

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": "_Test 3PL Client",
        "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups",
        "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories",
        "is_3pl_client": 1,
        "client_code": "TST",
    })
    customer.insert(ignore_permissions=True)
    return customer


def make_policy(policy_name, **kwargs):
    """Helper: build and return (without saving) an InventoryPolicy doc."""
    doc = frappe.get_doc({
        "doctype": "Inventory Policy",
        "policy_name": policy_name,
        "rotation_rule": "FIFO",
        "putaway_strategy": "Directed",
        "picking_strategy": "Single Order",
    })
    doc.update(kwargs)
    return doc


class TestInventoryPolicy(FrappeTestCase):

    def tearDown(self):
        # Clean up any policies created during tests
        for name in frappe.get_all("Inventory Policy", pluck="name"):
            frappe.delete_doc("Inventory Policy", name, force=True, ignore_missing=True)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 1: Create basic policy (no client, FIFO default)
    # ------------------------------------------------------------------
    def test_create_basic_policy(self):
        doc = make_policy("Basic FIFO Policy")
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Inventory Policy", "Basic FIFO Policy")
        self.assertEqual(saved.rotation_rule, "FIFO")
        self.assertEqual(saved.putaway_strategy, "Directed")
        self.assertEqual(saved.picking_strategy, "Single Order")
        self.assertFalse(saved.client)

    # ------------------------------------------------------------------
    # Test 2: Create client-specific policy (FEFO, Frozen zone, QC on)
    # ------------------------------------------------------------------
    def test_create_client_specific_policy(self):
        client = get_or_create_test_client()

        doc = make_policy(
            "Client Frozen FEFO Policy",
            client=client.name,
            rotation_rule="FEFO",
            temperature_zone="Frozen",
            qc_required=1,
            qc_sampling_pct=10.0,
        )
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Inventory Policy", "Client Frozen FEFO Policy")
        self.assertEqual(saved.client, client.name)
        self.assertEqual(saved.rotation_rule, "FEFO")
        self.assertEqual(saved.temperature_zone, "Frozen")
        self.assertTrue(saved.qc_required)
        self.assertEqual(saved.qc_sampling_pct, 10.0)

    # ------------------------------------------------------------------
    # Test 3: QC sampling validation — qc_required=1 but no sampling %
    # ------------------------------------------------------------------
    def test_qc_sampling_required_when_qc_enabled(self):
        doc = make_policy(
            "QC No Sampling Policy",
            qc_required=1,
            qc_sampling_pct=0,  # falsy — should trigger validation error
        )
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 4: Shelf life validation — value > 100 is invalid
    # ------------------------------------------------------------------
    def test_shelf_life_pct_over_100(self):
        doc = make_policy(
            "Bad Shelf Life Policy",
            min_remaining_shelf_life_pct=150.0,
        )
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)
