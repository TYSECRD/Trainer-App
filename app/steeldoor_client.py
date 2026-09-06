import os

import httpx


def send_security_event(
    source_ip: str,
    event_type: str,
    severity: str,
    description: str,
) -> bool:
    steeldoor_url = os.getenv("STEELDOOR_URL")
    steeldoor_api_key = os.getenv("STEELDOOR_API_KEY")

    if not steeldoor_url or not steeldoor_api_key:
        return False

    payload = {
        "source_ip": source_ip,
        "event_type": event_type,
        "severity": severity,
        "description": description,
    }

    headers = {
        "X-API-Key": steeldoor_api_key,
    }

    try:
        response = httpx.post(
            f"{steeldoor_url}/api/events",
            json=payload,
            headers=headers,
            timeout=3.0,
        )

        return response.status_code == 200

    except httpx.RequestError:
        return False