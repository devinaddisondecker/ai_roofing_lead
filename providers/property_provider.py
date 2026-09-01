import os
import httpx
import logging

logger = logging.getLogger(__name__)

DEMO_OWNER = {
    "owner": "John Smith",
    "email": "john.smith@example.com",
    "phone": "+1-801-555-0123",
    "property_type": "Single Family Residential",
    "year_built": 2005
}


async def lookup_owner(address: str):

    provider = os.getenv(
        "PROPERTY_PROVIDER",
        "demo"
    )


    if provider == "demo":
        return DEMO_OWNER


    if provider == "propertyradar":

        return await lookup_propertyradar(
            address
        )


    if provider == "attom":

        return await lookup_attom(
            address
        )


    raise Exception(
        "Unknown property provider"
    )



def split_address(address):
    """
    Split a free-text address into (street, city_state_zip) for
    APIs (like ATTOM) that want the two parts separately.

    Only splits on a comma ("123 Main St, Salt Lake City, UT 84104") --
    without one there's no reliable way to tell where the street name
    ends and the city begins (street suffixes like "Ave" or "Ct" look
    just like the start of a city name). Returns ("", "") when it can't
    confidently split, which callers should treat as "unable to look
    up" rather than guessing and querying a corrupted address.
    """

    address = address.strip()

    if "," not in address:
        return "", ""

    street, _, rest = address.partition(",")

    street = street.strip()
    rest = rest.strip()

    if not street or not rest:
        return "", ""

    return street, rest



async def lookup_propertyradar(address):

    # Confirmed against the live API (2026-08-31): endpoint is
    # POST /v1/properties with a Criteria body, Bearer auth. NOTE: the
    # free trial does NOT include API/integrations access at all --
    # every call 403s with "the integrations feature is not included
    # in the free trial", regardless of the body below. A paid
    # subscription is required to actually exercise this. The address
    # Criteria field name and response schema (owner/email/phone paths)
    # below are a best-effort based on PropertyRadar's public docs and
    # remain UNVERIFIED until called against an account with API access.
    # See https://developers.propertyradar.com/criteria

    api_key = os.getenv(
        "PROPERTYRADAR_API_KEY"
    )


    url = (
        "https://api.propertyradar.com/v1/properties"
    )


    headers = {
        "Authorization":
            f"Bearer {api_key}"
    }


    params = {
        "Purchase": 1
    }


    body = {
        "Criteria": [
            {
                "name": "Address",
                "value": [address]
            }
        ]
    }

    logger.info(
        f"Searching property data for: {address}"
    )

    async with httpx.AsyncClient() as client:

        response = await client.post(
            url,
            headers=headers,
            params=params,
            json=body
        )

        logger.info(
            f"PropertyRadar status: {response.status_code}"
        )

        logger.info(
            f"PropertyRadar response: {response.text}"
        )

        if response.status_code != 200:

            logger.warning(
                f"PropertyRadar lookup failed for '{address}' "
                f"(status={response.status_code}), "
                "falling back to demo owner data"
            )

            return DEMO_OWNER


        data = response.json()


    results = data.get("results", [])

    if not results:

        logger.warning(
            f"PropertyRadar found no match for '{address}', "
            "falling back to demo owner data"
        )

        return DEMO_OWNER


    property_data = results[0]


    return {

        "owner":
            property_data.get(
                "ownerName"
            ),

        "email":
            property_data.get(
                "ownerEmail"
            ),

        "phone":
            property_data.get(
                "ownerPhone"
            ),

        "property_type":
            property_data.get(
                "propertyType"
            ),

        "year_built":
            property_data.get(
                "yearBuilt"
            )
    }



async def lookup_attom(address):

    # https://api.developer.attomdata.com/docs
    # Free 30-day trial key: https://api.developer.attomdata.com

    api_key = os.getenv(
        "ATTOM_API_KEY"
    )

    if not api_key:

        logger.warning(
            "No ATTOM_API_KEY set, falling back to demo owner data"
        )

        return DEMO_OWNER


    street, city_state_zip = split_address(address)

    if not city_state_zip:

        logger.warning(
            f"Could not split '{address}' into street/city-state-zip "
            "for ATTOM, falling back to demo owner data"
        )

        return DEMO_OWNER


    url = (
        "https://api.gateway.attomdata.com"
        "/propertyapi/v1.0.0/property/detailowner"
    )


    headers = {
        "Accept": "application/json",
        "apikey": api_key
    }


    params = {
        "address1": street,
        "address2": city_state_zip
    }

    logger.info(
        f"Searching ATTOM property data for: {street} | {city_state_zip}"
    )

    async with httpx.AsyncClient() as client:

        response = await client.get(
            url,
            headers=headers,
            params=params
        )

        logger.info(
            f"ATTOM status: {response.status_code}"
        )

        logger.info(
            f"ATTOM response: {response.text}"
        )

        if response.status_code != 200:

            logger.warning(
                f"ATTOM lookup failed for '{address}' "
                f"(status={response.status_code}), "
                "falling back to demo owner data"
            )

            return DEMO_OWNER

        data = response.json()


    properties = data.get("property", [])

    if not properties:

        logger.warning(
            f"ATTOM found no match for '{address}', "
            "falling back to demo owner data"
        )

        return DEMO_OWNER


    property_data = properties[0]

    owner = property_data.get("owner", {})
    owner1 = owner.get("owner1", {})

    # ATTOM's exact owner field names vary by account/package;
    # this covers the shapes documented publicly. Check the logged
    # raw response above and adjust these paths if your account
    # returns a different structure.
    owner_name = (
        owner1.get("fullName")
        or owner1.get("lastName")
        or None
    )

    year_built = (
        property_data
        .get("summary", {})
        .get("yearBuilt")
    )

    property_type = (
        property_data
        .get("summary", {})
        .get("propType")
    )

    return {

        "owner": owner_name,

        "email": None,

        "phone": None,

        "property_type": property_type,

        "year_built": year_built
    }
