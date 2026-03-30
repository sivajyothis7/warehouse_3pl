import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase


def get_test_warehouse():
    """Return the first non-group warehouse from the DB."""
    return frappe.db.get_value("Warehouse", {"is_group": 0}, "name")


def make_location(zone="A", aisle="01", rack="R1", level="L1", bin_code="B001", **kwargs):
    warehouse = get_test_warehouse()
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
    return doc


class TestWarehouseLocation(FrappeTestCase):

    def tearDown(self):
        for name in frappe.get_all("Warehouse Location", pluck="name"):
            frappe.delete_doc("Warehouse Location", name, force=True, ignore_missing=True)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 1: Create location and verify defaults
    # ------------------------------------------------------------------
    def test_create_location_defaults(self):
        doc = make_location()
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Warehouse Location", doc.name)
        self.assertEqual(saved.location_type, "Reserve")
        self.assertEqual(saved.status, "Available")

    # ------------------------------------------------------------------
    # Test 2: Barcode auto-generated when empty
    # ------------------------------------------------------------------
    def test_barcode_auto_generated(self):
        doc = make_location(zone="B", aisle="02", rack="R2", level="L2", bin_code="B002")
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Warehouse Location", doc.name)
        self.assertEqual(saved.barcode, "B-02-R2-L2-B002")

    # ------------------------------------------------------------------
    # Test 3: Barcode not overwritten when explicitly set
    # ------------------------------------------------------------------
    def test_barcode_not_overwritten_when_set(self):
        doc = make_location(zone="C", aisle="03", rack="R3", level="L3", bin_code="B003")
        doc.barcode = "CUSTOM-BARCODE-001"
        doc.insert(ignore_permissions=True)

        saved = frappe.get_doc("Warehouse Location", doc.name)
        self.assertEqual(saved.barcode, "CUSTOM-BARCODE-001")

    # ------------------------------------------------------------------
    # Test 4: Negative max_weight_kg rejected
    # ------------------------------------------------------------------
    def test_negative_max_weight_rejected(self):
        doc = make_location(zone="D", aisle="04", rack="R4", level="L4", bin_code="B004")
        doc.max_weight_kg = -10.0
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 5: Negative max_volume_cbm rejected
    # ------------------------------------------------------------------
    def test_negative_max_volume_rejected(self):
        doc = make_location(zone="E", aisle="05", rack="R5", level="L5", bin_code="B005")
        doc.max_volume_cbm = -5.0
        with self.assertRaises(ValidationError):
            doc.insert(ignore_permissions=True)
