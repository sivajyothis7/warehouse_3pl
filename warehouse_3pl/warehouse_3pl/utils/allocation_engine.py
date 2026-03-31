import frappe
from warehouse_3pl.warehouse_3pl.utils.policy_engine import get_inventory_policy


def allocate_stock(client, item_code, qty, temperature_zone=None, lot_preference=None):
    """Allocate stock for picking based on FIFO/FEFO from Inventory Policy.
    Returns list of dicts: [{"warehouse": wh, "batch_no": lot, "qty": qty}, ...]
    """
    policy = get_inventory_policy(
        client=client,
        item_group=frappe.db.get_value("Item", item_code, "item_group"),
        temperature_zone=temperature_zone,
    )
    rotation_rule = policy.rotation_rule if policy else "FIFO"

    if lot_preference:
        allocated = _allocate_from_lot(item_code, lot_preference, qty)
        if allocated:
            return allocated

    bins = _get_available_bins(item_code, rotation_rule)
    allocations = []
    remaining = qty
    for b in bins:
        if remaining <= 0:
            break
        alloc_qty = min(remaining, b.get("actual_qty") or 0)
        if alloc_qty > 0:
            allocations.append({
                "warehouse": b.get("warehouse"),
                "batch_no": b.get("batch_no"),
                "qty": alloc_qty,
            })
            remaining -= alloc_qty
    return allocations


def _allocate_from_lot(item_code, lot_no, qty):
    """Try to allocate from a specific batch/lot using SLE balance."""
    # tabBin has no batch_no column; use SLE for batch-specific balance
    batch_bins = frappe.db.sql("""
        SELECT warehouse, SUM(actual_qty) as actual_qty
        FROM `tabStock Ledger Entry`
        WHERE item_code = %(item_code)s AND batch_no = %(lot_no)s
            AND is_cancelled = 0
        GROUP BY warehouse
        HAVING SUM(actual_qty) > 0
        ORDER BY SUM(actual_qty) DESC
    """, {"item_code": item_code, "lot_no": lot_no}, as_dict=True)

    allocations = []
    remaining = qty
    for b in batch_bins:
        if remaining <= 0:
            break
        alloc_qty = min(remaining, b.actual_qty)
        allocations.append({"warehouse": b.warehouse, "batch_no": lot_no, "qty": alloc_qty})
        remaining -= alloc_qty
    return allocations if remaining <= 0 else []


def _get_available_bins(item_code, rotation_rule):
    """Return available bin records ordered per rotation rule."""
    if rotation_rule == "FEFO":
        return frappe.db.sql("""
            SELECT bin.warehouse, bin.actual_qty, NULL as batch_no
            FROM `tabBin` bin
            WHERE bin.item_code = %(item_code)s AND bin.actual_qty > 0
            ORDER BY bin.warehouse ASC
        """, {"item_code": item_code}, as_dict=True)
    return frappe.db.sql("""
        SELECT warehouse, actual_qty, NULL as batch_no
        FROM `tabBin`
        WHERE item_code = %(item_code)s AND actual_qty > 0
        ORDER BY warehouse ASC
    """, {"item_code": item_code}, as_dict=True)
