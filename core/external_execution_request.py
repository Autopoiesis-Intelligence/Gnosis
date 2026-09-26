"""Explicit opt-in execution request derived from admitted information."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .external_operation import ExternalOperation
from .information_contract import Information


@dataclass(frozen=True)
class ExternalExecutionRequest:
    information_id: str
    operation: ExternalOperation
    content_digest: str
    purpose: str

    @classmethod
    def authorization_digest(self) -> str:
        """Stable digest identifying this exact authorization-bearing request."""
        payload = repr((
            self.information_id,
            self.operation.value,
            self.content_digest,
            self.purpose,
        )).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def from_information(
        cls,
        information: Information,
        *,
        operation: ExternalOperation,
        content_digest: str,
        purpose: str,
    ) -> "ExternalExecutionRequest":
        information.require_authorized()
        if not purpose.strip():
            raise ValueError("execution purpose is required")
        if not content_digest.strip():
            raise ValueError("content_digest is required")
        return cls(
            information_id=information.information_id,
            operation=operation,
            content_digest=content_digest,
            purpose=purpose,
        )
