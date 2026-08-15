
from core.logger import log

_VALIDATORS = []

def register_validator(fn):
    _VALIDATORS.append(fn)
    return fn

def run_all_validators(ctx):
    results = []
    for v_fn in _VALIDATORS:
        res = v_fn(ctx)
        results.append(res)
        status = "PASSED" if res.ok else "FAILED"
        log.info(f"Validator [{res.name}] -> {status} ({res.duration:.3f}s)")
        for err in res.errors:
            log.error(f"  - {err}")
        for warn in res.warnings:
            log.warn(f"  - {warn}")
    return results
