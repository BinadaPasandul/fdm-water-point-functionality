"""Known raw values verified against the fitted production pipeline vocabulary."""

from typing import Any


def option(label: str, value: str | int | float | None = None) -> dict[str, Any]:
    return {"label": label, "value": label if value is None else value}


YES_NO = [option("Yes"), option("No")]
REGIONS_BY_COUNTRY = {
    "Ethiopia": ["Tigray"],
    "India": ["Bihar", "West Bengal"],
    "Malawi": ["Central", "North", "South"],
    "Mali": ["Koulikoro", "Segou"],
    "Mozambique": ["Nampula", "Zambezia"],
    "Nepal": ["Central", "Western"],
    "Niger": ["Dosso", "Maradi"],
    "Rwanda": ["Northern Province"],
    "Uganda": ["Eastern"],
}

FIELD_OPTIONS: dict[str, list[dict[str, Any]]] = {
    "country": [option(value) for value in REGIONS_BY_COUNTRY],
    "admin1": [option(value) for regions in REGIONS_BY_COUNTRY.values() for value in regions],
    "cwfunded_wp": YES_NO,
    "wptype": [option(value) for value in [
        "Borehole with hand pump", "Mechanized borehole", "Piped water into yard / plot",
        "Protected dug well with hand pump", "Protected spring", "Public tap / standpipe",
        "Rainwater collection", "Unprotected dug well", "Unprotected spring",
    ]],
    "pumptype": [option(value) for value in [
        "Afridev", "Hydro India", "India Mark II", "U3", "Vergnet", "Vergnet Hydro", "Water4",
    ]],
    "drillmethod": [option(value) for value in [
        "Drilled by machine", "Hand-dug", "Manually drilled",
    ]],
    "piped_source": [option(value) for value in ["Borehole", "Protected spring", "Unprotected spring"]],
    "piped_pump": [option(value) for value in [
        "Diesel powered pump", "Electric powered pump", "Gravity Fed", "Solar powered pump",
    ]],
    "rehabyn": YES_NO,
    "whomanage_wp": [option(value) for value in [
        "Church", "Community leader", "District/local government", "Don't Know",
        "Health administrator", "No one", "Other", "Private person", "School", "Vendor", "Water committee",
    ]],
    "lockedfullday_wp": YES_NO,
    "wc_present_wp": YES_NO,
    "paytocollect_wp": YES_NO,
    "improved_wponly_wp": [option("No", 0), option("Yes", 1)],
    "wc_admin_index_wp": [option(value) for value in ["Inadequate", "Minimum", "Moderate", "Advanced"]],
    "wc_finance_index_wp": [option(value) for value in ["Inadequate", "Minimum", "Moderate", "Advanced"]],
    "wc_mgmt_index_wp": [option(value) for value in ["Inadequate", "Minimum", "Moderate", "Advanced"]],
    "wc_maint_index_wp": [option(value) for value in ["Inadequate", "Minimum", "Moderate", "Advanced"]],
    "wc_savings_wp": [option("No", 0), option("Yes", 1)],
    "season": [option("Dry", "dry"), option("Wet", "wet")],
}

DEPENDENT_OPTIONS = {"admin1": {country: [option(region) for region in regions]
                                for country, regions in REGIONS_BY_COUNTRY.items()}}
