import os
import httpx
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

async def get_roof_measurement(address):

    logger.info(
        f"Starting roof analysis for: {address}"
    )

    location = await geocode(address)

    logger.info(
        f"Geocode response: {location}"
    )


    solar = await get_solar(
        location["lat"],
        location["lng"]
    )


    logger.info(
        f"Solar API response: {solar}"
    )


    return solar



async def geocode(address):


    api_key = os.getenv(
        "GOOGLE_MAPS_API_KEY"
    )


    if not api_key:

        return {
            "lat":40.7608,
            "lng":-111.8910
        }



    url = (
        "https://maps.googleapis.com/maps/api/geocode/json"
    )


    params = {
        "address": address,
        "key": api_key
    }


    async with httpx.AsyncClient() as client:

        response = await client.get(
            url,
            params=params
        )
        
        # logger.info(
        #     f"Google Geocode status: {response.status_code}"
        # )

        # logger.info(
        #     f"Google Geocode response: {response.text}"
        # )

        data=response.json()


    results = data.get("results", [])

    if response.status_code != 200 or not results:

        logger.warning(
            f"Geocode failed for '{address}' "
            f"(status={data.get('status')}, "
            f"error={data.get('error_message')}), "
            "falling back to demo coordinates"
        )

        return {
            "lat":40.7608,
            "lng":-111.8910
        }


    location = (
        results[0]
        ["geometry"]
        ["location"]
    )


    return {

        "lat":
            location["lat"],

        "lng":
            location["lng"]

    }




async def get_solar(lat,lng):


    api_key=os.getenv(
        "GOOGLE_MAPS_API_KEY"
    )


    if not api_key:

        return {
            "roof_area_sqft":2385,
            "roof_segments":7,
            "roof_quality":"HIGH",
            "pitch":28
        }



    url=(
        "https://solar.googleapis.com/"
        "v1/buildingInsights:findClosest"
    )


    params={

        "location.latitude":lat,

        "location.longitude":lng,

        "requiredQuality":"HIGH",

        "key":api_key
    }



    async with httpx.AsyncClient() as client:

        response=await client.get(
            url,
            params=params
        )

        # logger.info(
        #     f"Google Solar status: {response.status_code}"
        # )

        # logger.info(
        #     f"Google Solar response: {response.text}"
        # )

        if response.status_code != 200:

            logger.warning(
                f"Solar API failed (status={response.status_code}), "
                "falling back to demo roof data"
            )

            return {
                "roof_area_sqft":2385,
                "roof_segments":7,
                "roof_quality":"HIGH",
                "pitch":28
            }

        data=response.json()



    segments = (
        data
        .get("solarPotential",{})
        .get("roofSegmentStats",[])
    )


    total_area = sum(

        x
        .get("stats",{})
        .get("areaMeters2",0)

        for x in segments

    )


    pitches = [
        x.get("pitchDegrees")
        for x in segments
        if x.get("pitchDegrees") is not None
    ]

    avg_pitch = (
        round(sum(pitches) / len(pitches))
        if pitches
        else None
    )


    return {

        "roof_area_sqft":
            round(
                total_area * 10.7639
            ),

        "roof_segments":
            len(segments),

        "roof_quality":
            data.get(
                "imageryQuality"
            ),

        "pitch":
            avg_pitch
    }