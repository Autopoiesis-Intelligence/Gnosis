# Gnozis Internet Interoperability Port — M1

## Purpose

The Internet Port is the protocol boundary between Gnozis and external AI/agent systems. It is an interoperability layer, not part of the mathematical core.

The port must allow an external system to:

1. identify the protocol and capabilities;
2. submit an observation, hypothesis, request or candidate state transformation;
3. receive a deterministic machine-readable result;
4. preserve provenance and session/context boundaries;
5. fail closed when authorization/context requirements are not satisfied.

## Boundary

```text
External AI / Agent
        |
        v
   Internet Port
        |
   Adapter / validation
        |
        v
   Gnozis Core
        |
        v
   Port Response
```

The external model is never the hidden global selector of the Gnozis core. The port may transport a proposal or request; acceptance remains governed by the core contract.

## M1 protocol surface

### GET /health
Returns liveness and protocol identity.

Example:

```json
{"status":"online","core":"ready"}
```

### POST /chat
Compatibility endpoint for the current experimental CoreChat adapter. It is not the normative interoperability protocol; it is retained for backwards compatibility.

### POST /v1/handshake
Establishes a protocol session. A client supplies a protocol version and client identity/provenance. The server returns accepted protocol version and a session identifier.

### POST /v1/exchange
Carries one structured message through the port. Required fields:

```json
{
  "protocol": "gnozis-port/1",
  "session_id": "...",
  "message_id": "...",
  "type": "observation|hypothesis|request|candidate",
  "payload": {},
  "provenance": {}
}
```

Responses are structured and must contain:

```json
{
  "protocol": "gnozis-port/1",
  "message_id": "...",
  "status": "accepted|rejected|error",
  "reason": "...",
  "result": {}
}
```

## Browser origin policy

Cross-origin browser access is disabled by default. To allow specific browser
origins, set `GNOZIS_PORT_ALLOWED_ORIGINS` to a comma-separated list of exact
origins, for example `https://console.example,https://partner.example`.
Wildcard entries are ignored. This is a browser policy only, not authentication
or authorization; it does not make the endpoint safe for public deployment.

## Security model

The port is not considered Internet-safe merely because it speaks HTTP.

Every POST endpoint requires an HTTP `Authorization: Bearer <token>` header
matched against the server-side `GNOZIS_PORT_API_TOKEN` secret. If the secret
is not configured, POST requests fail closed with HTTP 503; missing or invalid
tokens receive HTTP 401. The client-supplied `authorization` object inside a
message is not transport authentication. `GET /health` remains an unauthenticated
liveness endpoint and is not proof that the service is production-ready.

This single shared bearer token is a minimum transport gate, not a complete
identity, per-client authorization, key rotation, or deployment-isolation system.

Before public deployment it requires at minimum:

- TLS termination;
- authentication/credential validation;
- replay protection;
- request size limits;
- rate limiting;
- explicit origin/CORS policy;
- structured audit logging without secrets;
- session expiry;
- fail-closed authorization;
- no direct arbitrary execution endpoint.

The existing challenge mechanism provides a basis for context binding and replay resistance, but it does not by itself constitute complete Internet authentication.

## Non-goals

M1 does not claim:

- autonomous Internet agency;
- trust in arbitrary external AI systems;
- public unauthenticated deployment;
- scientific validation of Gnozis;
- replacement of the Gnozis core with an LLM.

## M1 acceptance criteria

- protocol is explicitly versioned;
- every exchange has a message/session identity;
- malformed requests fail closed;
- unsupported protocol versions are rejected;
- session mismatch is rejected;
- replayed message identifiers are rejected;
- provenance survives the adapter boundary;
- external input cannot directly mutate hidden core state;
- the same protocol can be implemented by GPT, Claude, Gemini or another agent without changing the core.
