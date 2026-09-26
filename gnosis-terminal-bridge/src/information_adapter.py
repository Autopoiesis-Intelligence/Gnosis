from __future__ import annotations

from typing import Any

from core.external_operation import parse_external_operation
from core.information_contract import (
    Authorization,
    AuthorizationStatus,
    Information,
    ValueClass,
)


def information_from_exchange(envelope: dict[str, Any]) -> Information:
    """Convert a validated transport envelope into an explicitly authorized input."""
    authorization = envelope.get("authorization")
    if not isinstance(authorization, dict):
        raise PermissionError("authorization required")

    status_raw = authorization.get("status")
    try:
        status = AuthorizationStatus(status_raw)
    except (TypeError, ValueError):
        status = AuthorizationStatus.UNKNOWN

    operation = parse_external_operation(str(authorization.get("operation", "")))
    info = Information(
        information_id=str(envelope["message_id"]),
        source=str(authorization.get("source", "")),
        content_reference=str(envelope["payload_sha256"]),
        provenance_ref=str(envelope["provenance"]),
        authorization=Authorization(
            source=str(authorization.get("source", "")),
            purpose=str(authorization.get("purpose", "")),
            operation=operation.value,
            destination=str(authorization.get("destination", "")),
            status=status,
            validity_ref=(
                str(authorization["validity_ref"])
                if authorization.get("validity_ref") is not None
                else None
            ),
        ),
        value_class=ValueClass.UNKNOWN,
        payload=envelope["payload"],
    )
    info.require_authorized()
    return info
