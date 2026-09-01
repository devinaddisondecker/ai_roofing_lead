import os
import logging

from anthropic import AsyncAnthropic


logger = logging.getLogger(__name__)


async def score_lead(owner, roof):

    api_key = os.getenv(
        "ANTHROPIC_API_KEY"
    )

    # If no API key or no credits, use fallback
    if not api_key:
        return fallback_score(owner, roof)


    try:

        client = AsyncAnthropic(
            api_key=api_key
        )


        response = await client.messages.create(

            model="claude-3-5-sonnet-20241022",

            max_tokens=500,

            messages=[
                {
                    "role": "user",
                    "content": f"""
Analyze this roofing lead.

Owner:
{owner}

Roof:
{roof}

Return:
- lead score 0-100
- reason
"""
                }
            ]
        )


        return response.content[0].text


    except Exception as e:

        logger.warning(
            f"Claude unavailable: {e}"
        )

        return fallback_score(
            owner,
            roof
        )



def fallback_score(owner, roof):

    score = 0
    reasons = []


    roof_area = roof.get(
        "roof_area_sqft",
        0
    )


    if roof_area > 2000:

        score += 40

        reasons.append(
            "Large roof size"
        )


    if owner.get(
        "property_type"
    ) == "Single Family Residential":

        score += 30

        reasons.append(
            "Residential property"
        )


    year = owner.get(
        "year_built",
        2020
    )


    if year < 2010:

        score += 30

        reasons.append(
            "Older property"
        )


    return {

        "lead_score": score,

        "reason": ", ".join(
            reasons
        )

    }