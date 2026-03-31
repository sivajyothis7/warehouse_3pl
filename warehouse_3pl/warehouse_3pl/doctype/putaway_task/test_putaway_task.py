import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase

# Tell the test runner not to auto-create test records for these linked doctypes
# (avoids deep dependency chains for doctypes not relevant to our tests)
test_ignore = [
    "User",
    "Warehouse",
    "Stock Entry",
    "Payment Gateway",
    "Payment Gateway Account",
    "Currency",
    "Mode of Payment",
    "Fiscal Year",
    "Account",
    "Cost Center",
]


def _get_test_customer():
    """Return existing test customer or create a new one (idempotent)."""
    name = "_Test Putaway Client"
    if frappe.db.exists("Customer", name):
        return frappe.get_doc("Customer", name)
    return frappe.get_doc({
        "doctype": "Customer",
        "customer_name": name,
        "customer_type": "Company",
        "customer_group": "All Customer Groups",
        "territory": "All Territories",
        "is_3pl_client": 1,
        "client_code": "TPUT",
    }).insert(ignore_permissions=True)


def _get_test_item():
    """Return existing test item or create a new one (idempotent)."""
    code = "_Test Putaway Item"
    if frappe.db.exists("Item", code):
        return frappe.get_doc("Item", code)
    return frappe.get_doc({
        "doctype": "Item",
        "item_code": code,
        "item_name": code,
        "item_group": "All Item Groups",
        "stock_uom": "Nos",
        "is_stock_item": 1,
    }).insert(ignore_permissions=True)


def _ensure_wh(short_name):
    """Return the full warehouse name (appending company abbreviation if needed)."""
    # Check if warehouse already exists by the exact name
    if frappe.db.exists("Warehouse", short_name):
        return short_name
    # Try appending the default company abbreviation
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    abbr = frappe.db.get_value("Company", company, "abbr") if company else None
    if abbr:
        full_name = f"{short_name} - {abbr}"
        if frappe.db.exists("Warehouse", full_name):
            return full_name
    # Create it
    wh = frappe.get_doc({
        "doctype": "Warehouse",
        "warehouse_name": short_name,
        "company": company,
    }).insert(ignore_permissions=True)
    return wh.name


def _add_stock(item, qty, warehouse):
    """Create and submit a Material Receipt to put stock in a warehouse."""
    company = frappe.db.get_value("Warehouse", warehouse, "company")
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company": company,
        "items": [{
            "item_code": item,
            "qty": qty,
            "t_warehouse": warehouse,
            "basic_rate": 1.0,
            "allow_zero_valuation_rate": 1,
        }],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    return se


class TestPutawayTask(FrappeTestCase):

    def setUp(self):
        self.customer = _get_test_customer()
        self.item = _get_test_item()
        self.source_wh = _ensure_wh("_Test Putaway Staging")
        self.target_wh = _ensure_wh("_Test Putaway Bin")
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    # ------------------------------------------------------------------
    # Test 1: Create a putaway task — verify status is Pending
    # ------------------------------------------------------------------
    def test_create_putaway_task(self):
        task = frappe.get_doc({
            "doctype": "Putaway Task",
            "client": self.customer.name,
            "item_code": self.item.item_code,
            "qty": 10.0,
            "source_location": self.source_wh,
            "target_location": self.target_wh,
        })
        task.insert(ignore_permissions=True)
        self.assertEqual(task.status, "Pending")

    # ------------------------------------------------------------------
    # Test 2: complete() creates a Material Transfer Stock Entry
    # ------------------------------------------------------------------
    def test_complete_creates_stock_transfer(self):
        # Add stock to source warehouse first
        _add_stock(self.item.item_code, 20.0, self.source_wh)
        frappe.db.commit()

        task = frappe.get_doc({
            "doctype": "Putaway Task",
            "client": self.customer.name,
            "item_code": self.item.item_code,
            "qty": 10.0,
            "source_location": self.source_wh,
            "target_location": self.target_wh,
        })
        task.insert(ignore_permissions=True)
        frappe.db.commit()

        task.complete()

        # Reload to verify db_set fields
        task.reload()
        self.assertEqual(task.status, "Complete")
        self.assertIsNotNone(task.completed_at)
        self.assertIsNotNone(task.stock_entry)

        # Verify the linked SE
        se = frappe.get_doc("Stock Entry", task.stock_entry)
        self.assertEqual(se.stock_entry_type, "Material Transfer")
        self.assertEqual(se.docstatus, 1)  # submitted

    # ------------------------------------------------------------------
    # Test 3: Zero qty is rejected on insert
    # ------------------------------------------------------------------
    def test_zero_qty_rejected(self):
        task = frappe.get_doc({
            "doctype": "Putaway Task",
            "client": self.customer.name,
            "item_code": self.item.item_code,
            "qty": 0,
            "source_location": self.source_wh,
            "target_location": self.target_wh,
        })
        with self.assertRaises(ValidationError):
            task.insert(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Test 4: Calling complete() twice raises ValidationError
    # ------------------------------------------------------------------
    def test_already_complete_rejected(self):
        # Add stock so the first complete() succeeds
        _add_stock(self.item.item_code, 20.0, self.source_wh)
        frappe.db.commit()

        task = frappe.get_doc({
            "doctype": "Putaway Task",
            "client": self.customer.name,
            "item_code": self.item.item_code,
            "qty": 5.0,
            "source_location": self.source_wh,
            "target_location": self.target_wh,
        })
        task.insert(ignore_permissions=True)
        frappe.db.commit()

        task.complete()
        task.reload()

        with self.assertRaises(ValidationError):
            task.complete()
