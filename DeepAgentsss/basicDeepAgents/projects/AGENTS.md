# AGENTS.md

## Project Context
This project explores building AI agents using DeepAgents, LangGraph, PostgreSQL, persistent stores, checkpointing, and virtual filesystem backends.

## Before Making Changes
- Inspect the existing code and relevant library versions before modifying anything.
- Understand the current implementation before proposing a rewrite.
- Prefer explaining and fixing the root cause over applying workarounds.
- Do not assume an API exists; verify it against the installed package or official documentation.
- Preserve working code and existing behavior unless the requested change requires otherwise.

## Coding Guidelines
- Use Python and follow PEP 8 conventions.
- Keep implementations simple, readable, and focused on the requested task.
- Avoid unnecessary abstractions, dependencies, files, and refactoring.
- Reuse existing project patterns where appropriate.
- Handle errors explicitly; do not silently suppress exceptions.
- Never claim code has been tested unless it has actually been run.

## DeepAgents and LangGraph
- Follow the APIs supported by the installed DeepAgents and LangGraph versions.
- Distinguish filesystem backends, long-term stores, and conversation checkpointers.
- Do not assume that virtual files are physical files on the operating system.
- Verify namespace behavior and user isolation when working with StoreBackend.
- Configure a checkpointer explicitly when persistent conversation checkpoints are required.
- Keep database connections and other resources open for the duration of their use.
- Do not change backend architecture or persistence behavior without a clear reason.

## PostgreSQL and Security
- Read database configuration from environment variables; never hardcode credentials.
- Never expose secrets in logs, source code, or generated documentation.
- Do not drop databases, truncate tables, delete persistent data, or run destructive migrations without explicit user approval.
- Preserve user and thread isolation.
- Do not treat a user ID supplied by an untrusted client as proof of authorization.

## Verification
- Inspect the relevant tests and project configuration before choosing verification commands.
- Run focused tests for the modified behavior.
- Check imports, syntax, and relevant type or lint checks when available.
- For persistence changes, verify behavior across separate invocations and, where relevant, separate threads.
- For namespace changes, verify that different users cannot access each other's stored data.
- If verification cannot be completed, state what remains unverified.

## Scope Control
- Make only changes needed to satisfy the request.
- Do not overwrite user work or modify unrelated files.
- Ask before making consequential architectural decisions when the requirements are unclear.
- Explain important changes and report the actual verification results in the final response.
