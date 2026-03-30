import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


def get_or_create_3pl_client():
    """Return existing test 3PL client or create a new one."""
    if frappe.db.exists("Customer", "_Test 3PL Client"):
        return frappe.get_doc("Customer", "_Test 3PL Client")

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": "_Test 3PL Client",
        "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups",
        "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories",
        "is_3pl_client": 1,
    })
    customer.insert(ignore_permissions=True)
    return customer


def get_or_create_non_3pl_client():
    """Return a non-3PL customer."""
    if frappe.db.exists("Customer", "_Test Non-3PL Client"):
        return frappe.get_doc("Customer", "_Test Non-3PL Client")

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": "_Test Non-3PL Client",
        "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups",
        "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories",
        "is_3pl_client": 0,
    })
    customer.insert(ignore_permissions=True)
    return customer


def get_test_item():
    """Return the first available item."""
    return frappe.db.get_value("Item", {"disabled": 0}, "name")


class TestClientItem(FrappeTestCase):

    def setUp(self):
        self.client_3pl = get_or_create_3pl_client()
        self.client_non_3pl = get_or_create_non_3pl_client()
        self.item = get_test_item()

    def tearDown(self):
        for name in frappe.get_all("Client Item", pluck="name"):
            frappe.delete_doc("Client Item", name, force=True, ignore_missing=True)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 1: Create client item for valid 3PL client
    # ------------------------------------------------------------------
    def test_create_client_item(self):
        doc = frappe.get_doc({
            "doctype": "Client Item",
            "client": self.client_3pl.name,
            "item_code": self.item,
            "client_sku": "SKU-001",
            "velocity_class": "A",
        })
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Client Item", doc.name)
        self.assertEqual(saved.client, self.client_3pl.name)
        self.assertEqual(saved.item_code, self.item)
        self.assertEqual(saved.client_sku, "SKU-001")
        self.assertEqual(saved.velocity_class, "A")

    # ------------------------------------------------------------------
    # Test 2: Non-3PL client is rejected
    # ------------------------------------------------------------------
    def test_non_3pl_client_rejected(self):
        doc = frappe.get_doc({
            "doctype": "Client Item",
            "client": self.client_non_3pl.name,
            "item_code": self.item,
        })
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 3: Optional fields default to empty / None
    # ------------------------------------------------------------------
    def test_optional_fields_empty_by_default(self):
        doc = frappe.get_doc({
            "doctype": "Client Item",
            "client": self.client_3pl.name,
            "item_code": self.item,
        })
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Client Item", doc.name)
        self.assertFalse(saved.client_sku)
        self.assertFalse(saved.storage_temp_required)
        self.assertFalse(saved.rotation_rule)
        self.assertFalse(saved.velocity_class)
