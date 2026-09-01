"""
GST-related utility functions.

Central place for the compliance logic we scoped across the conversation:
- Determining IGST vs CGST+SGST based on supplier/customer state codes
- Zero-rating exports under LUT
- Financial year labelling (April-to-March, matches invoice numbering)
"""
from datetime import date

# Official GST state codes (first 2 digits of any GSTIN)
GST_STATE_CODES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
    "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "25": "Daman and Diu", "26": "Dadra and Nagar Haveli",
    "27": "Maharashtra", "28": "Andhra Pradesh (Old)", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana",
    "37": "Andhra Pradesh", "38": "Ladakh",
}


def extract_state_code(gstin: str) -> str:
    """First 2 characters of a GSTIN are the state code."""
    if not gstin or len(gstin) < 2:
        return ""
    return gstin[:2]


def state_name_from_code(code: str) -> str:
    return GST_STATE_CODES.get(code, "Unknown")


def determine_tax_type(supplier_gstin: str, customer_gstin: str, is_export: bool) -> str:
    """
    Returns one of: 'IGST_ZERO' (export under LUT), 'IGST' (inter-state),
    'CGST_SGST' (intra-state).

    This is the core fix from our compliance review: invoices were
    previously showing a generic "GST" figure regardless of whether the
    supply was inter-state or intra-state, which is not legally correct.
    """
    if is_export:
        return "IGST_ZERO"

    supplier_state = extract_state_code(supplier_gstin)
    customer_state = extract_state_code(customer_gstin)

    if not customer_state or supplier_state == customer_state:
        return "CGST_SGST"
    return "IGST"


def financial_year_label(for_date: date) -> str:
    """April-to-March FY, e.g. 2026-08-31 -> '2026-27', 2027-02-15 -> '2026-27'."""
    if for_date.month >= 4:
        start_year = for_date.year
    else:
        start_year = for_date.year - 1
    end_year_short = str((start_year + 1) % 100).zfill(2)
    return f"{start_year}-{end_year_short}"
