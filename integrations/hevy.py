from __future__ import annotations

import json
import math
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .dtos import (
    AccountDTO,
    ExerciseTemplateDTO,
    PayloadError,
    RoutineDTO,
    RoutineFolderDTO,
    WorkoutDTO,
    WorkoutEventDTO,
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def urlopen(request, timeout):
    return build_opener(NoRedirect()).open(request, timeout=timeout)


class HevyError(RuntimeError):
    def __init__(self, code: str, message: str, *, retries: int = 0):
        super().__init__(message)
        self.code = code
        self.retries = retries


@dataclass(frozen=True)
class PageResult:
    items: tuple[dict[str, Any], ...]
    requested_pages: int
    received_pages: int


Transport = Callable[[str, dict[str, str], float], tuple[int, dict[str, str], bytes]]
WriteTransport = Callable[
    [str, dict[str, str], bytes, float],
    tuple[int, dict[str, str], bytes],
]


def default_transport(url: str, headers: dict[str, str], timeout: float):
    request = Request(url, headers=headers, method='GET')
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read(5 * 1024 * 1024 + 1)
    except HTTPError as error:
        return error.code, dict(error.headers.items()), error.read(5 * 1024 * 1024 + 1)
    except URLError as error:
        raise TimeoutError from error


def default_write_transport(
    url: str, headers: dict[str, str], body: bytes, timeout: float, method: str = 'POST'
):
    request = Request(url, headers=headers, data=body, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read(5 * 1024 * 1024 + 1)
    except HTTPError as error:
        return error.code, dict(error.headers.items()), error.read(5 * 1024 * 1024 + 1)
    except URLError as error:
        raise TimeoutError from error


class HevyClient:
    BASE_URL = 'https://api.hevyapp.com/'
    TIMEOUT_SECONDS = 30
    MAX_ATTEMPTS = 3
    MAX_RESPONSE_BYTES = 5 * 1024 * 1024
    PAGE_SIZES = {
        'exercise_templates': 100,
        'routine_folders': 10,
        'routines': 10,
        'workouts': 10,
        'workout_events': 10,
    }
    COLLECTION_KEYS = {
        'exercise_templates': 'exercise_templates',
        'routine_folders': 'routines',
        'routines': 'routines',
        'workouts': 'workouts',
    }
    ALLOWED_PATHS = {
        '/v1/user/info', '/v1/exercise_templates', '/v1/routine_folders',
        '/v1/routines', '/v1/workouts', '/v1/workouts/events',
    }

    def __init__(self, api_key: str, base_url: str = BASE_URL, *,
                 transport: Transport = default_transport,
                 write_transport: WriteTransport = default_write_transport,
                 sleep: Callable[[float], None] = time.sleep,
                 jitter: Callable[[], float] = random.random):
        if not api_key.strip():
            raise HevyError('CONFIG_MISSING_KEY', 'Hevy API key is not configured.')
        parsed = urlparse(base_url)
        if parsed.scheme != 'https' or parsed.netloc != 'api.hevyapp.com' or parsed.path not in {'', '/'}:
            raise HevyError('CONFIG_INVALID_HOST', 'Hevy API host is not allowed.')
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip('/') + '/'
        self.transport = transport
        self.write_transport = write_transport
        self.sleep = sleep
        self.jitter = jitter
        self.retry_count = 0
        self.captured_pages = {}
        self.cached_catalog_pages = None

    @classmethod
    def from_environment(cls, **kwargs: Any) -> HevyClient:
        return cls(os.environ.get('HEVY_API_KEY', ''), os.environ.get('HEVY_API_BASE_URL', cls.BASE_URL), **kwargs)

    @classmethod
    def for_user(cls, user):
        from integrations.credentials import key_for_user
        return cls(key_for_user(user) or '')

    def _get(self, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
        parts = path.split('/')
        dynamic_workout = (
            len(parts) == 4
            and parts[:3] in (['', 'v1', 'workouts'], ['', 'v1', 'routines'])
            and bool(parts[3])
            and re.fullmatch(r'[A-Za-z0-9_-]+', parts[3]) is not None
        )
        if path not in self.ALLOWED_PATHS and not dynamic_workout:
            raise HevyError('HTTP_PERMANENT', 'Hevy endpoint is not allowlisted.')
        url = urljoin(self.base_url, path.lstrip('/'))
        if query:
            url = f'{url}?{urlencode(query)}'
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                status, headers, body = self.transport(url, {'api-key': self.api_key, 'Accept': 'application/json'}, self.TIMEOUT_SECONDS)
            except (TimeoutError, OSError):
                status, headers, body = 408, {}, b''
            if 200 <= status < 300:
                if len(body) > self.MAX_RESPONSE_BYTES:
                    raise HevyError('PAYLOAD_INVALID', 'Hevy response exceeds the size limit.', retries=self.retry_count)
                try:
                    payload = json.loads(body)
                except (TypeError, json.JSONDecodeError) as error:
                    raise HevyError('PAYLOAD_INVALID', 'Hevy returned invalid JSON.', retries=self.retry_count) from error
                if not isinstance(payload, dict):
                    raise HevyError('PAYLOAD_INVALID', 'Hevy returned an invalid response.', retries=self.retry_count)
                return payload
            retryable = status == 408 or status == 429 or 500 <= status < 600
            if not retryable or attempt == self.MAX_ATTEMPTS:
                code = 'AUTH_INVALID' if status in {401, 403} else ('HTTP_TIMEOUT' if status == 408 else ('HTTP_TRANSIENT' if retryable else 'HTTP_PERMANENT'))
                raise HevyError(code, f'Hevy request failed with HTTP {status}.', retries=self.retry_count)
            self.retry_count += 1
            delay = headers.get('Retry-After') if status == 429 else None
            try:
                retry_after = float(delay) if delay is not None else None
                if retry_after is not None and (not math.isfinite(retry_after) or retry_after < 0):
                    raise ValueError
                wait = min(retry_after, 30) if retry_after is not None else 2 ** (attempt - 1) + self.jitter()
            except (TypeError, ValueError, OverflowError):
                wait = 2 ** (attempt - 1) + self.jitter()
            self.sleep(wait)
        raise AssertionError('unreachable')

    @staticmethod
    def _decode_payload(body: bytes) -> dict[str, Any]:
        if len(body) > HevyClient.MAX_RESPONSE_BYTES:
            raise HevyError('PAYLOAD_INVALID', 'Hevy response exceeds the size limit.')
        try:
            payload = json.loads(body)
        except (TypeError, json.JSONDecodeError) as error:
            raise HevyError('PAYLOAD_INVALID', 'Hevy returned invalid JSON.') from error
        if not isinstance(payload, dict):
            raise HevyError('PAYLOAD_INVALID', 'Hevy returned an invalid response.')
        return payload

    def get_routine_payload(self, routine_id):
        if not isinstance(routine_id, str) or re.fullmatch(r'[A-Za-z0-9_-]+', routine_id) is None:
            raise HevyError('PAYLOAD_INVALID', 'Invalid routine identifier.')
        response = self._get('/v1/routines/' + routine_id)
        routine = response.get('routine', response)
        try:
            if not isinstance(routine, dict):
                raise PayloadError('Expected a routine object.')
            dto = RoutineDTO.from_payload(routine)
            if dto.external_id != routine_id:
                raise PayloadError('Routine identity mismatch.')
        except (PayloadError, TypeError) as error:
            raise HevyError('PAYLOAD_INVALID', 'Invalid routine response.') from error
        return routine

    def update_routine(self, routine_id, payload):
        if not isinstance(routine_id, str) or re.fullmatch(r'[A-Za-z0-9_-]+', routine_id) is None:
            raise HevyError('PAYLOAD_INVALID', 'Invalid routine identifier.')
        return self._write_routine(payload, routine_id)

    def create_routine(self, payload: dict[str, Any]) -> RoutineDTO:
        return self._write_routine(payload)

    def _write_routine(self, payload, routine_id=None):
        """Create one routine without automatically retrying an ambiguous write."""
        url = urljoin(self.base_url, 'v1/routines' + ('/' + routine_id if routine_id else ''))
        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
        if len(body) > 65_536:
            raise HevyError('PAYLOAD_INVALID', 'Routine payload exceeds the size limit.')
        headers = {
            'api-key': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        try:
            if routine_id:
                status, _, response_body = self.write_transport(
                    url, headers, body, self.TIMEOUT_SECONDS, method='PUT'
                )
            else:
                status, _, response_body = self.write_transport(url, headers, body, self.TIMEOUT_SECONDS)
        except (TimeoutError, OSError) as error:
            raise HevyError(
                'WRITE_UNKNOWN',
                'Hevy did not confirm whether the routine was applied.',
            ) from error
        if 200 <= status < 300:
            try:
                response = self._decode_payload(response_body)
                routine = response.get('routine', response)
                if not isinstance(routine, dict):
                    raise HevyError(
                        'PAYLOAD_INVALID', 'Hevy returned an invalid routine response.'
                    )
                dto = RoutineDTO.from_payload(routine)
                if routine_id and dto.external_id != routine_id:
                    raise PayloadError('Routine identity mismatch.')
                return dto
            except (HevyError, PayloadError) as error:
                raise HevyError(
                    'WRITE_UNKNOWN',
                    'Hevy accepted the request but returned an invalid confirmation.',
                ) from error
        if status in {401, 403}:
            raise HevyError('AUTH_INVALID', f'Hevy request failed with HTTP {status}.')
        if status == 408 or status >= 500:
            raise HevyError(
                'WRITE_UNKNOWN',
                'Hevy did not confirm whether the routine was applied.',
            )
        raise HevyError('HTTP_PERMANENT', f'Hevy request failed with HTTP {status}.')

    def user_info(self) -> AccountDTO:
        try:
            return AccountDTO.from_payload(self._get('/v1/user/info'))
        except PayloadError as error:
            raise HevyError('PAYLOAD_INVALID', str(error), retries=self.retry_count) from error

    def pages(self, collection: str) -> PageResult:
        if collection == 'exercise_templates' and self.cached_catalog_pages is not None:
            pages = self.cached_catalog_pages
            items = tuple(item for page in pages for item in page['exercise_templates'])
            return PageResult(items, len(pages), len(pages))
        path = f'/v1/{collection}'
        item_key = self.COLLECTION_KEYS[collection]
        page = 1
        page_count: int | None = None
        items: list[dict[str, Any]] = []
        raw_pages = []
        while page_count is None or page <= page_count:
            payload = self._get(path, {'page': page, 'pageSize': self.PAGE_SIZES[collection]})
            current = payload.get('page')
            total = payload.get('page_count')
            received = payload.get(item_key)
            if type(current) is not int or type(total) is not int or current != page or total < page or not isinstance(received, list) or not all(isinstance(item, dict) for item in received):
                raise HevyError('PAGINATION_INVALID', 'Hevy returned invalid pagination metadata.', retries=self.retry_count)
            if page_count is not None and total != page_count:
                raise HevyError('PAGINATION_INVALID', 'Hevy pagination changed during retrieval.', retries=self.retry_count)
            page_count = total
            items.extend(received)
            raw_pages.append(payload)
            page += 1
        self.captured_pages[collection] = raw_pages
        return PageResult(tuple(items), requested_pages=page_count or 0, received_pages=page_count or 0)

    def full_import_payload(self):
        templates = self.pages('exercise_templates')
        folders = self.pages('routine_folders')
        routines = self.pages('routines')
        workouts = self.pages('workouts')
        try:
            return (
                tuple(ExerciseTemplateDTO.from_payload(item) for item in templates.items),
                tuple(RoutineFolderDTO.from_payload(item) for item in folders.items),
                tuple(RoutineDTO.from_payload(item) for item in routines.items),
                tuple(WorkoutDTO.from_payload(item) for item in workouts.items),
                {
                    'exercise_templates': {'requested': templates.requested_pages, 'received': templates.received_pages},
                    'routine_folders': {'requested': folders.requested_pages, 'received': folders.received_pages},
                    'routines': {'requested': routines.requested_pages, 'received': routines.received_pages},
                    'workouts': {'requested': workouts.requested_pages, 'received': workouts.received_pages},
                },
            )
        except PayloadError as error:
            raise HevyError('PAYLOAD_INVALID', str(error), retries=self.retry_count) from error

    def plans_payload(self):
        templates = self.pages('exercise_templates')
        folders = self.pages('routine_folders')
        routines = self.pages('routines')
        try:
            return (
                tuple(ExerciseTemplateDTO.from_payload(item) for item in templates.items),
                tuple(RoutineFolderDTO.from_payload(item) for item in folders.items),
                tuple(RoutineDTO.from_payload(item) for item in routines.items),
                {
                    'exercise_templates': {'requested': templates.requested_pages, 'received': templates.received_pages},
                    'routine_folders': {'requested': folders.requested_pages, 'received': folders.received_pages},
                    'routines': {'requested': routines.requested_pages, 'received': routines.received_pages},
                },
            )
        except PayloadError as error:
            raise HevyError('PAYLOAD_INVALID', str(error), retries=self.retry_count) from error

    def workout_events(self, since: datetime) -> PageResult:
        if since.tzinfo is None:
            raise HevyError('PAYLOAD_INVALID', 'Workout event cursor must be timezone-aware.')
        page = 1
        page_count: int | None = None
        items = []
        query_since = since.astimezone(UTC).isoformat().replace('+00:00', 'Z')
        while page_count is None or page <= page_count:
            payload = self._get('/v1/workouts/events', {'since': query_since, 'page': page, 'pageSize': self.PAGE_SIZES['workout_events']})
            current = payload.get('page')
            total = payload.get('page_count')
            received = payload.get('events')
            if type(current) is not int or type(total) is not int or current != page or total < page or not isinstance(received, list) or not all(isinstance(item, dict) for item in received):
                raise HevyError('PAGINATION_INVALID', 'Hevy returned invalid workout-event pagination.', retries=self.retry_count)
            if page_count is not None and total != page_count:
                raise HevyError('PAGINATION_INVALID', 'Hevy workout-event pagination changed during retrieval.', retries=self.retry_count)
            page_count = total
            items.extend(received)
            page += 1
        try:
            return PageResult(tuple(WorkoutEventDTO.from_payload(item) for item in items), page_count or 0, page_count or 0)
        except PayloadError as error:
            raise HevyError('PAYLOAD_INVALID', str(error), retries=self.retry_count) from error

    def get_workout(self, external_id: str) -> WorkoutDTO:
        if not external_id or '/' in external_id:
            raise HevyError('PAYLOAD_INVALID', 'Workout ID is invalid.')
        try:
            return WorkoutDTO.from_payload(self._get(f'/v1/workouts/{quote(external_id, safe="")}'))
        except PayloadError as error:
            raise HevyError('PAYLOAD_INVALID', str(error), retries=self.retry_count) from error
