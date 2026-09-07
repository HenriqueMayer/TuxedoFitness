"""Content versions for local assets, including development without collectstatic."""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from django.contrib.staticfiles import finders
from django.templatetags.static import static

FRONTEND_ASSETS = (
    "css/app.css",
    "js/navigation.js",
    "js/charts.js",
    "js/fitness.js",
    "js/theme.js",
    "js/theme-bootstrap.js",
    "js/mobile-menu.js",
    "js/sync-actions.js",
)


@lru_cache(maxsize=128)
def _digest(path, modified, size):
    return sha256(Path(path).read_bytes()).hexdigest()[:16]


def asset_version(name):
    path = Path(finders.find(name))
    stat = path.stat()
    return _digest(str(path), stat.st_mtime_ns, stat.st_size)


def versioned_static(name):
    return f"{static(name)}?v={asset_version(name)}"


def frontend_version():
    return sha256("".join(map(asset_version, FRONTEND_ASSETS)).encode()).hexdigest()[
        :16
    ]
