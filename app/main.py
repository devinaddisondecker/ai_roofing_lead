import json
import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from providers.property_provider import lookup_owner
from services.roof import get_roof_measurement
from services.lead_scoring import score_lead
from services.email_ai import generate_email
from services.crm_export import build_crm_payload

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Roofing Lead Generator POC"
)

templates = Jinja2Templates(
    directory="templates"
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": None
        }
    )


@app.post("/", response_class=HTMLResponse)
async def analyze(
    request: Request,
    address: str = Form(...)
):

    logger.info(
        f"Received analyze request for: {address}"
    )

    # 1. Get owner/contact data
    owner = await lookup_owner(address)

    logger.info(
        f"Owner lookup response: {owner}"
    )

    # 2. Get roof information
    roof = await get_roof_measurement(address)

    logger.info(
        f"Roof measurement response: {roof}"
    )

    # 3. AI lead qualification
    lead = await score_lead(
        owner,
        roof
    )

    logger.info(
        f"Lead scoring response: {lead}"
    )

    # 4. Generate outreach email
    email = await generate_email(
        owner,
        roof,
        lead
    )

    logger.info(
        f"Generated email response: {email}"
    )

    # 5. Structured payload for CRM / quote system
    crm_payload = build_crm_payload(
        address,
        owner,
        roof,
        lead
    )

    logger.info(
        f"CRM export payload: {crm_payload}"
    )

    result = {
        "address": address,
        **owner,
        **roof,
        **lead,
        "email_message": email,
        "crm_payload_json": json.dumps(crm_payload, indent=2)
    }

    logger.info(
        f"Final result response: {result}"
    )

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": result
        }
    )