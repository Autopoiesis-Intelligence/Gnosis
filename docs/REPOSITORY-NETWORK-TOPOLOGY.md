# Gnozis Repository Network — Canonical Role Topology

## Naming rule

Repository names describe stable architectural roles, not implementation versions. Do not use V2/V3 naming.

## Canonical topology

```
                         Gnozis Network
                              |
                    +---------+---------+
                    |                   |
              Public Surface       Main Core
                    |                   |
          +---------+---------+    Network Registry
          |         |         |    Policy / Authority
       Research  Knowledge  Partner   Governance
       Workers   Libraries   Surfaces
          |         |         |
          +---------+---------+
                    |
             Specialized Cores
                    |
             Protected Genesis
```

## Repository roles

### 1. Gnozis
Public product surface and human-facing entry point. Contains public-facing documentation, navigation, evidence views and stable product semantics. It is not the canonical authority state of the protected Core.

### 2. Gnozis-Research
Public research/work repository family. Handles Internet research, source collection, analysis outputs, evidence packaging and research workflows. Heavy work stays outside Main Core.

### 3. Gnozis-Knowledge-<domain>
Machine-readable knowledge libraries organized by stable scientific/domain role: mathematics, physics, history, psychology, maps of discoveries, and future domains. These are attachable network resources, not authority over Core state.

### 4. Gnozis-Partner-<name>
Partner-facing work surfaces. A partner may operate a scoped CRM Core for its team or client work. Partner data remains tenant-scoped.

### 5. Gnozis-Core-<specialization>
Specialized Core repositories. Created because a distinct capability or sustained operational need exists, not merely because Main Core needs more compute. Each Core has explicit admission, capability, privacy and routing contracts.

### 6. Gnozis-Core
The protected Main Core / network authority. Coordinates the network, admission, routing, authorization, canonical state, evidence, governance and evolution. It should not perform public Internet research or bulk repository work.

### 7. Genesis
Private machine factory / commercial protected layer. Produces specialized modules, scoped proposals and commercial/private Core configurations. Genesis is not the public source of truth.

## Trust rule

```
Public repository -> untrusted input/result
Research output   -> evidence candidate
Knowledge library -> network resource
Partner surface   -> tenant-scoped request/result
Specialized Core  -> bounded execution authority
Main Core         -> canonical authority
Genesis           -> private module factory
```

No public repository becomes trusted merely because the Main Core generated or updated it.

## Machine-managed network

The Main Core may create, populate, update, archive and connect downstream repositories through controlled ports. Repository existence, content and routing remain subject to policy, provenance and audit.

Manual work should be limited to stable semantic decisions that cannot be safely inferred: repository role, public/private boundary, ownership, naming and policy intent.

## Workload rule

Internet retrieval, large-scale analysis, document processing, repository generation and public catalogue maintenance execute in workers/specialized layers. The Main Core coordinates, scopes, authorizes and verifies; it does not absorb those workloads.

## Evolution rule

A new Specialized Core is proposed when a distinct capability is needed. A patch is proposed when analytics identify an optimization. Both pass through testing, policy, evidence and controlled rollout before affecting canonical operation.
