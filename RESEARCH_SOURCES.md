# Verified external research sources

These are public GitHub repositories verified as reachable through the connected GitHub source layer. They are research references only; do not add them as runtime dependencies without a separate architectural decision.

## Agent orchestration
- https://github.com/openai/openai-agents-python — OpenAI Agents SDK; multi-agent workflows, tools, handoffs, guardrails, sessions and tracing.
- https://github.com/langchain-ai/langgraph — stateful/graph-based agent execution and resilient agent workflows.
- https://github.com/microsoft/autogen — multi-agent orchestration patterns. Note: the repository is now in maintenance mode; Microsoft recommends Microsoft Agent Framework for new projects.

## Durable execution / transport
- https://github.com/temporalio/temporal — durable execution, workflow recovery and distributed workflow patterns.
- https://github.com/modelcontextprotocol/servers — MCP server implementations and external-tool integration patterns.

## Infrastructure / contracts
- https://github.com/fastapi/fastapi — API and async transport patterns suitable for Gnosis adapters and services.
- https://github.com/pydantic/pydantic — typed validation and state/data contracts.
- https://github.com/open-telemetry/opentelemetry-specification — tracing and observability standards.

## Knowledge / retrieval
- https://github.com/qdrant/qdrant — vector search/storage patterns.
- https://github.com/neo4j/neo4j — graph database and knowledge-graph patterns.
- https://github.com/deepset-ai/haystack — modular retrieval, pipelines and evaluation patterns.

## Persistence
- https://github.com/sqlite/sqlite — SQLite source and persistence behavior; relevant when evaluating SQLite/WAL persistence for Gnosis components.

## Research rule
Use these repositories as comparative architectural references. Reachability is not an endorsement, security audit, dependency decision or proof that a Gnosis integration exists. Record exact source revision, intended use, license, data/permission boundary, maintenance status and reproducible evaluation before adopting an external component.

**Naming rule:** current product/repository identity is Gnosis; the protected engineering repository is Gnosis-Core; the research/context layer is Gnosis-Memory. Legacy labels should appear only when identifying historical artifacts.
