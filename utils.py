import pycountry  # Import pycountry library for country code lookups

def get_country_code(user_input: str) -> str:
    """
    Convert a country name or code to ISO alpha-2.
    Returns "" for worldwide or if lookup fails.
    """
    if not user_input:  # Check if input is empty or None
        return ""  # Return empty string for worldwide/no country
    s = user_input.strip()  # Remove leading/trailing whitespace
    if len(s) == 2 and s.isalpha():  # Check if input is a 2-letter code
        return s.upper()  # Return uppercase version of the code
    try:
        country = pycountry.countries.lookup(s)  # Attempt to lookup country by name
        return country.alpha_2  # Return the 2-letter country code
    except Exception:  # Handle any lookup errors
        return ""  # Return empty string on failure