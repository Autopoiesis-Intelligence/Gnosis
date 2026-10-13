# Gnosis Terminal Bridge

Minimal experimental terminal bridge for Ψ-GNR.

## Purpose

The bridge provides a controlled interface between an external terminal and Gnosis.

Current experimental functionality:

- ephemeral challenge generation;
- challenge verification;
- context binding;
- replay protection;
- expiration;
- fail-closed rejection.

## Current status

This repository is NOT the Gnosis core.

It is an experimental bridge for validating the terminal protocol.

## Protocol chain

P
→ Γ
→ Ω
→ F
→ JΨ
→ λΨ
→ Ψ-GNR

## Agency chain

SOURCE
→ EVIDENCE
→ AUTHORITY
→ AGENCY
→ CAPABILITY
→ SESSION
→ CHANNEL

## Security principle

Discovery ≠ Authorization

Potential Agency ≠ Active Agency

History ≠ Current Authority

Channel ≠ Identity

Session ≠ Agency

## Current milestone

M0:

- generation fence;
- epoch fence;
- provenance;
- authority boundary;
- challenge verification;
- replay protection;
- fail-closed behavior.
