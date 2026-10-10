"""Job registry. Jobs are discovered by importing every module in ``config.job_modules``."""

import importlib
import pkgutil
from collections.abc import Callable

from backend.jobs.base import Job

_REGISTRY: dict[str, type[Job]] = {}


class JobNotFoundError(KeyError):
    pass


def register_job(name: str) -> Callable[[type[Job]], type[Job]]:
    def decorator(cls: type[Job]) -> type[Job]:
        if not name or not name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid job name: {name!r}")
        existing = _REGISTRY.get(name)
        if existing is not None and existing is not cls:
            raise ValueError(f"Job {name!r} already registered by {existing.__module__}")
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_job(name: str) -> type[Job]:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise JobNotFoundError(name) from None


def list_jobs() -> dict[str, type[Job]]:
    return dict(sorted(_REGISTRY.items()))


def discover_jobs(packages: str) -> None:
    """Import all modules of the comma-separated packages so @register_job runs."""
    for package_name in [p.strip() for p in packages.split(",") if p.strip()]:
        package = importlib.import_module(package_name)
        for module in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
            importlib.import_module(module.name)
