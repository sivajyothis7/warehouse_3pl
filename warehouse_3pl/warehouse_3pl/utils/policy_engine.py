import frappe


def get_inventory_policy(client=None, item_group=None, temperature_zone=None):
    """Resolve the most specific Inventory Policy matching the given parameters.

    Resolution priority (highest to lowest):
    1. client + item_group + temperature_zone
    2. client + item_group
    3. client + temperature_zone
    4. client only
    5. System default (no client)

    Within each tier, higher priority value wins.
    Returns the Inventory Policy document or None if no policy exists.
    """
    filters_tiers = _build_filter_tiers(client, item_group, temperature_zone)

    for filters in filters_tiers:
        policies = frappe.get_all(
            "Inventory Policy",
            filters=filters,
            fields=["name"],
            order_by="priority desc",
            limit=1,
        )
        if policies:
            return frappe.get_doc("Inventory Policy", policies[0].name)

    return None


def _build_filter_tiers(client, item_group, temperature_zone):
    """Build filter tiers from most specific to least specific."""
    tiers = []

    # Tier 1: client + item_group + temperature_zone
    if client and item_group and temperature_zone:
        tiers.append({
            "client": client,
            "item_group": item_group,
            "temperature_zone": temperature_zone,
        })

    # Tier 2: client + item_group
    if client and item_group:
        tiers.append({
            "client": client,
            "item_group": item_group,
            "temperature_zone": ("is", "not set"),
        })

    # Tier 3: client + temperature_zone
    if client and temperature_zone:
        tiers.append({
            "client": client,
            "temperature_zone": temperature_zone,
            "item_group": ("is", "not set"),
        })

    # Tier 4: client only
    if client:
        tiers.append({
            "client": client,
            "temperature_zone": ("is", "not set"),
            "item_group": ("is", "not set"),
        })

    # Tier 5: system default (no client)
    tiers.append({
        "client": ("is", "not set"),
        "temperature_zone": ("is", "not set"),
        "item_group": ("is", "not set"),
    })

    return tiers
