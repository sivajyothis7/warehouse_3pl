import frappe
from frappe.tests.utils import FrappeTestCase

from warehouse_3pl.warehouse_3pl.utils.putaway_engine import suggest_putaway_location


def _get_test_warehouse():
    """Return the first non-group warehouse from the DB."""
    return frappe.db.get_value("Warehouse", {"is_group": 0}, "name")


def _make_location(zone, aisle, rack, level, bin_code, **kwargs):
    """Insert a Warehouse Location and return the doc."""
    warehouse = _get_test_warehouse()
    doc = frappe.get_doc({
        "doctype": "Warehouse Location",
        "warehouse": warehouse,
        "zone": zone,
        "aisle": aisle,
        "rack": rack,
        "level": level,
        "bin_code": bin_code,
    })
    doc.update(kwargs)
    doc.insert(ignore_permissions=True)
    return doc


def _get_company_warehouse():
    """Return a Warehouse that belongs to the first Company."""
    company = frappe.get_all("Company", limit=1)[0].name
    abbr = frappe.db.get_value("Company", company, "abbr")
    wh = frappe.db.get_value("Warehouse", {"is_group": 0, "company": company}, "name")
    if not wh:
        # Fallback: create a minimal warehouse
        wh_doc = frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": f"Test Putaway Warehouse",
            "company": company,
        })
        wh_doc.insert(ignore_permissions=True)
        wh = wh_doc.name
    return wh


class TestPutawayEngine(FrappeTestCase):

    def tearDown(self):
        for name in frappe.get_all("Warehouse Location", pluck="name"):
            frappe.delete_doc("Warehouse Location", name, force=True, ignore_missing=True)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 1: Given an available location, returns its warehouse
    # ------------------------------------------------------------------
    def test_suggest_location_returns_warehouse(self):
        loc = _make_location("PA", "01", "R1", "L1", "B001", status="Available")
        result = suggest_putaway_location(
            client="__any_client__",
            item_code="__any_item__",
            qty=1,
        )
        self.assertEqual(result, loc.warehouse)

    # ------------------------------------------------------------------
    # Test 2: Prefers Frozen location when Frozen temp zone is requested
    # ------------------------------------------------------------------
    def test_suggest_location_respects_temp_zone(self):
        _make_location("PB", "01", "R1", "L1", "B002", status="Available", temperature_zone="Ambient")
        frozen_loc = _make_location("PB", "02", "R2", "L2", "B003", status="Available", temperature_zone="Frozen")
        result = suggest_putaway_location(
            client="__any_client__",
            item_code="__any_item__",
            qty=1,
            temperature_zone="Frozen",
        )
        self.assertEqual(result, frozen_loc.warehouse)

    # ------------------------------------------------------------------
    # Test 3: Prefers client-dedicated location
    # ------------------------------------------------------------------
    def test_suggest_location_respects_client_zone(self):
        company = frappe.get_all("Company", limit=1)[0].name
        if not frappe.db.exists("Customer", "_Test Putaway Client"):
            frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "_Test Putaway Client",
                "customer_type": "Company",
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
                "is_3pl_client": 1,
                "client_code": "TPUT",
            }).insert(ignore_permissions=True)

        # Shared location
        _make_location("PC", "01", "R1", "L1", "B004", status="Available")
        # Client-dedicated location
        client_loc = _make_location(
            "PC", "02", "R2", "L2", "B005",
            status="Available",
            owning_client="_Test Putaway Client",
        )

        result = suggest_putaway_location(
            client="_Test Putaway Client",
            item_code="__any_item__",
            qty=1,
        )
        self.assertEqual(result, client_loc.warehouse)

    # ------------------------------------------------------------------
    # Test 4: Returns None when no locations exist for nonexistent client
    # ------------------------------------------------------------------
    def test_suggest_location_returns_none_when_no_locations(self):
        # No Warehouse Location records exist (tearDown clears them)
        result = suggest_putaway_location(
            client="_Nonexistent Client XYZ_99",
            item_code="__any_item__",
            qty=1,
        )
        self.assertIsNone(result)
