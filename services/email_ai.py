import os
import logging

from anthropic import AsyncAnthropic


logger = logging.getLogger(__name__)


async def generate_email(owner, roof, lead):

    api_key = os.getenv(
        "ANTHROPIC_API_KEY"
    )


    try:

        if not api_key:
            raise Exception(
                "No Anthropic API key"
            )


        client = AsyncAnthropic(
            api_key=api_key
        )


        response = await client.messages.create(

            # update this model later if needed
            model="claude-3-5-sonnet-20240620",

            max_tokens=500,

            messages=[
                {
                    "role":"user",
                    "content":f"""
Create a roofing sales email.

Homeowner:
{owner}

Roof:
{roof}

Lead score:
{lead}

Make it short and friendly.
"""
                }
            ]
        )


        return response.content[0].text


    except Exception as e:

        logger.warning(
            f"Claude email unavailable: {e}"
        )

        return fallback_email(
            owner,
            roof,
            lead
        )



def fallback_email(owner, roof, lead):

    name = owner.get(
        "owner",
        "Homeowner"
    )


    area = roof.get(
        "roof_area_sqft",
        "unknown"
    )


    score = lead.get(
        "lead_score",
        0
    )


    return f"""
Subject: Free Roof Inspection Available


Hi {name},


We are helping Salt Lake City homeowners
with professional roof inspections.


Based on available property information,
your roof is approximately {area} sq ft.


Your property appears to be a good candidate
for a roof evaluation.


Lead score: {score}/100


Would you like to schedule a free inspection?


Best regards,

Roof Team
"""