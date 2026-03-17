from urllib.parse import urlencode

from django.core import signing


REPORT_EVIDENCE_LINK_SALT = "apps.car.report_evidence_link"
REPORT_EVIDENCE_LINK_MAX_AGE_SECONDS = 60 * 60


def build_report_evidence_token(evidence_id, car_id) -> str:
    """Create a short-lived signed token for exported report evidence links."""
    return signing.dumps(
        {
            "evidence_id": str(evidence_id),
            "car_id": str(car_id),
        },
        salt=REPORT_EVIDENCE_LINK_SALT,
        compress=True,
    )


def build_report_evidence_url(request, evidence_id, car_id) -> str:
    """Build an absolute evidence-view URL that can be embedded in exports."""
    query = urlencode(
        {
            "report_token": build_report_evidence_token(evidence_id, car_id),
        }
    )
    return request.build_absolute_uri(f"/api/psc/evidence/{evidence_id}/view/?{query}")


def is_valid_report_evidence_token(
    token: str | None,
    *,
    evidence_id,
    car_id,
    max_age: int = REPORT_EVIDENCE_LINK_MAX_AGE_SECONDS,
) -> bool:
    """Validate a signed report evidence token against the expected evidence/CAR ids."""
    if not token:
        return False

    try:
        payload = signing.loads(
            token,
            salt=REPORT_EVIDENCE_LINK_SALT,
            max_age=max_age,
        )
    except signing.BadSignature:
        return False
    except signing.SignatureExpired:
        return False

    return (
        str(payload.get("evidence_id")) == str(evidence_id)
        and str(payload.get("car_id")) == str(car_id)
    )