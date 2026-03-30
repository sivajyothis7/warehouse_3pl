import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from warehouse_3pl.warehouse_3pl.doctype.rate_card.rate_card import get_rate


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
    })
    customer.insert(ignore_permissions=True)
    return customer


def make_rate_card(client, effective_from, status="Draft", effective_to=None, lines=None):
    if lines is None:
        lines = [
            {"activity_type": "Receiving", "uom": "Per Pallet", "rate": 10.0, "minimum_charge": 50.0},
        ]
    doc = frappe.get_doc({
        "doctype": "Rate Card",
        "client": client,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "status": status,
        "rate_lines": lines,
    })
    return doc


class TestRateCard(FrappeTestCase):

    def setUp(self):
        self.client = get_or_create_test_client()

    def tearDown(self):
        for name in frappe.get_all("Rate Card", pluck="name"):
            frappe.delete_doc("Rate Card", name, force=True, ignore_missing=True)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 1: Create rate card with lines
    # ------------------------------------------------------------------
    def test_create_rate_card(self):
        doc = make_rate_card(
            client=self.client.name,
            effective_from=today(),
            lines=[
                {"activity_type": "Receiving", "uom": "Per Pallet", "rate": 12.5, "minimum_charge": 50.0},
                {"activity_type": "Storage", "uom": "Per Month", "rate": 5.0},
            ]
        )
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Rate Card", doc.name)
        self.assertEqual(saved.status, "Draft")
        self.assertEqual(len(saved.rate_lines), 2)
        self.assertEqual(saved.rate_lines[0].activity_type, "Receiving")
        self.assertEqual(saved.rate_lines[0].rate, 12.5)

    # ------------------------------------------------------------------
    # Test 2: effective_to before effective_from is rejected
    # ------------------------------------------------------------------
    def test_date_validation(self):
        doc = make_rate_card(
            client=self.client.name,
            effective_from=today(),
            effective_to=add_days(today(), -1),
        )
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 3: Duplicate activity/uom combination rejected
    # ------------------------------------------------------------------
    def test_duplicate_activity_rejected(self):
        doc = make_rate_card(
            client=self.client.name,
            effective_from=today(),
            lines=[
                {"activity_type": "Receiving", "uom": "Per Pallet", "rate": 10.0},
                {"activity_type": "Receiving", "uom": "Per Pallet", "rate": 15.0},
            ]
        )
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 4: Same activity with different UOM is allowed
    # ------------------------------------------------------------------
    def test_same_activity_different_uom_allowed(self):
        doc = make_rate_card(
            client=self.client.name,
            effective_from=today(),
            lines=[
                {"activity_type": "Receiving", "uom": "Per Pallet", "rate": 10.0},
                {"activity_type": "Receiving", "uom": "Per Unit", "rate": 2.0},
            ]
        )
        doc.insert(ignore_permissions=True)
        saved = frappe.get_doc("Rate Card", doc.name)
        self.assertEqual(len(saved.rate_lines), 2)

    # ------------------------------------------------------------------
    # Test 5: get_rate utility returns correct rate for active card
    # ------------------------------------------------------------------
    def test_get_rate_utility(self):
        doc = make_rate_card(
            client=self.client.name,
            effective_from=add_days(today(), -5),
            status="Active",
            lines=[
                {"activity_type": "Picking", "uom": "Per Order", "rate": 7.5, "minimum_charge": 20.0},
            ]
        )
        doc.insert(ignore_permissions=True)

        rate, min_charge = get_rate(self.client.name, "Picking", uom="Per Order")
        self.assertEqual(rate, 7.5)
        self.assertEqual(min_charge, 20.0)

    # ------------------------------------------------------------------
    # Test 6: get_rate returns 0,0 when no active rate card
    # ------------------------------------------------------------------
    def test_get_rate_no_active_card(self):
        rate, min_charge = get_rate(self.client.name, "Shipping")
        self.assertEqual(rate, 0)
        self.assertEqual(min_charge, 0)
