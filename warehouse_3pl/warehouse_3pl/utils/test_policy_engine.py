import frappe
from frappe.tests.utils import FrappeTestCase

from warehouse_3pl.warehouse_3pl.utils.policy_engine import get_inventory_policy


class TestPolicyEngine(FrappeTestCase):
    def setUp(self):
        # Create test customer
        if not frappe.db.exists("Customer", "_Test Policy Client"):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "_Test Policy Client",
                "customer_type": "Company",
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
                "is_3pl_client": 1,
                "client_code": "TPOL",
            })
            customer.insert(ignore_permissions=True)

        # Create test item group
        if not frappe.db.exists("Item Group", "_Test Food"):
            item_group = frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": "_Test Food",
                "parent_item_group": "All Item Groups",
            })
            item_group.insert(ignore_permissions=True)

        # Create policies
        if not frappe.db.exists("Inventory Policy", "PE Default"):
            frappe.get_doc({
                "doctype": "Inventory Policy",
                "policy_name": "PE Default",
                "priority": 0,
                "rotation_rule": "FIFO",
                "putaway_strategy": "Directed",
                "picking_strategy": "Single Order",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Inventory Policy", "PE Client Only"):
            frappe.get_doc({
                "doctype": "Inventory Policy",
                "policy_name": "PE Client Only",
                "client": "_Test Policy Client",
                "priority": 5,
                "rotation_rule": "FIFO",
                "putaway_strategy": "Client Zone",
                "picking_strategy": "Batch",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Inventory Policy", "PE Client Zone"):
            frappe.get_doc({
                "doctype": "Inventory Policy",
                "policy_name": "PE Client Zone",
                "client": "_Test Policy Client",
                "temperature_zone": "Frozen",
                "priority": 10,
                "rotation_rule": "FEFO",
                "putaway_strategy": "Directed",
                "picking_strategy": "Single Order",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Inventory Policy", "PE Client Group Zone"):
            frappe.get_doc({
                "doctype": "Inventory Policy",
                "policy_name": "PE Client Group Zone",
                "client": "_Test Policy Client",
                "temperature_zone": "Frozen",
                "item_group": "_Test Food",
                "priority": 20,
                "rotation_rule": "FEFO",
                "putaway_strategy": "Consolidate",
                "picking_strategy": "Zone",
                "qc_required": 1,
                "qc_sampling_pct": 100,
            }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_most_specific_match(self):
        """client + _Test Food + Frozen should return PE Client Group Zone"""
        policy = get_inventory_policy(
            client="_Test Policy Client",
            item_group="_Test Food",
            temperature_zone="Frozen",
        )
        self.assertIsNotNone(policy)
        self.assertEqual(policy.name, "PE Client Group Zone")

    def test_client_zone_match(self):
        """client + All Item Groups + Frozen should return PE Client Zone"""
        policy = get_inventory_policy(
            client="_Test Policy Client",
            item_group="All Item Groups",
            temperature_zone="Frozen",
        )
        self.assertIsNotNone(policy)
        self.assertEqual(policy.name, "PE Client Zone")

    def test_client_only_match(self):
        """client + Ambient (no zone match) should return PE Client Only"""
        policy = get_inventory_policy(
            client="_Test Policy Client",
            temperature_zone="Ambient",
        )
        self.assertIsNotNone(policy)
        self.assertEqual(policy.name, "PE Client Only")

    def test_fallback_to_default(self):
        """Nonexistent client should fall back to PE Default"""
        policy = get_inventory_policy(
            client="_NonExistent Client XYZ",
        )
        self.assertIsNotNone(policy)
        self.assertEqual(policy.name, "PE Default")

    def test_no_policy_returns_none(self):
        """After deleting all policies, nonexistent client should return None"""
        for policy_name in ["PE Default", "PE Client Only", "PE Client Zone", "PE Client Group Zone"]:
            if frappe.db.exists("Inventory Policy", policy_name):
                frappe.delete_doc("Inventory Policy", policy_name, ignore_permissions=True)

        policy = get_inventory_policy(client="_NonExistent Client XYZ")
        self.assertIsNone(policy)
