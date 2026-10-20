# Python Instructions

## Code style
- Follow PEP 8; use black/ruff formatting
- Type annotate public functions; use `from __future__ import annotations` if needed
- Prefer pathlib over os.path; use context managers for resources

## Common patterns
- Dataclasses for DTOs: `@dataclass(frozen=True)`
- Context managers via `contextlib.contextmanager`
- Async: `asyncio.gather` for concurrency; avoid blocking in event loop
- Error handling: raise specific exceptions; never bare `except`

## Testing
- pytest with fixtures; parametrize with `@pytest.mark.parametrize`
- Use `tmp_path` fixture for filesystem tests
- Mock with `unittest.mock.patch`

## Performance
- Use generators for large data; `itertools` for pipelines
- Profile with `cProfile`/`py-spy`; avoid global state
