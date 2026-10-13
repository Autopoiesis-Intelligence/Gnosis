# Gnosis Provenance Contract v1

## Purpose
Every material information transformation must remain traceable to authorized inputs and the operation that produced it.

## Minimum provenance
- provenance_id
- input_information_ids
- source_reference
- authorization_reference
- operation
- actor_or_module
- sequence_or_timestamp
- output_information_id
- evidence_reference
- integrity_digest when available

## Rules
1. Provenance is append-oriented; historical evidence is not silently rewritten.
2. An output cannot claim stronger authorization than its relevant inputs.
3. Transformation does not erase source provenance.
4. Repository storage does not convert provenance into authority.
5. Replay must reconstruct the claimed derivation from recorded evidence.
6. Missing provenance means UNKNOWN provenance, not implied trust.
7. External repositories may provide evidence but cannot silently become Core authority.

## Acceptance
A conforming processing path can identify the inputs, authorization context, operation, and resulting output for every material derived information object.
