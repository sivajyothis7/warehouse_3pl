import frappe


def suggest_putaway_location(client, item_code, qty, temperature_zone=None, lot_no=None):
    """Suggest the best warehouse bin for putaway.
    Priority: 1) Client-dedicated zone with temp match, 2) Client-dedicated zone,
    3) Temp zone match (shared), 4) Any available location.
    Returns ERPNext Warehouse name or None."""

    # Client-dedicated + temperature match
    if temperature_zone:
        location = _find_location(owning_client=client, temperature_zone=temperature_zone, status="Available")
        if location:
            return location

    # Client-dedicated (any temp)
    location = _find_location(owning_client=client, status="Available")
    if location:
        return location

    # Temperature match (shared locations)
    if temperature_zone:
        location = _find_location(temperature_zone=temperature_zone, status="Available", no_owning_client=True)
        if location:
            return location

    # Any available
    location = _find_location(status="Available")
    if location:
        return location

    return None


def _find_location(owning_client=None, temperature_zone=None, status="Available", no_owning_client=False):
    filters = {"status": status}
    if owning_client:
        filters["owning_client"] = owning_client
    elif no_owning_client:
        filters["owning_client"] = ("is", "not set")
    if temperature_zone:
        filters["temperature_zone"] = temperature_zone
    location = frappe.db.get_value("Warehouse Location", filters, "warehouse", order_by="name asc")
    return location
