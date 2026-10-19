# Python Best Practices

- Prefer explicit over implicit; readable code over clever
- Keep functions small and single-purpose
- Use type hints; run mypy/pyright in CI
- Pin dependencies; use lockfiles
- Write tests for public APIs; aim for deterministic tests
- Avoid mutable default arguments
- Use `__slots__` for memory-heavy classes
- Log with `logging`, not print, in libraries
- Never commit secrets; use env vars
