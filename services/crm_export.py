def build_crm_payload(address, owner, roof, lead):

    return {
        "customer": owner.get("owner"),
        "address": address,
        "roof_size": roof.get("roof_area_sqft"),
        "email": owner.get("email"),
        "phone": owner.get("phone"),
        "lead_score": lead.get("lead_score")
    }
