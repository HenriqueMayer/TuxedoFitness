# Access and conventions

## Authentication

The key is available in Hevy Web under `Settings > Developer` and requires
Hevy Pro. Store it only in the backend secret store or environment; never put
it in the repository, client application, logs, URL, or documentation.

```bash
export HEVY_API_KEY='replace-with-a-real-key'
export HEVY_API_BASE_URL='https://api.hevyapp.com'
```

Every request uses the `api-key` HTTP header:

```bash
curl --fail-with-body --silent --show-error \
  -H "api-key: $HEVY_API_KEY" \
  "$HEVY_API_BASE_URL/v1/user/info"
```

The snapshot does not document a `Bearer` prefix; the header above is the
documented contract.

## Formats and units

- Workout and routine IDs are strings; do not coerce them to numbers.
- Exercise-template IDs are strings. Routine-folder IDs are numbers.
- Timestamps are ISO 8601, for example `2024-08-14T12:00:00Z`.
- Body measurements use `YYYY-MM-DD` only.
- Use `weight_kg`, `distance_meters`, and `duration_seconds` as canonical
  integration units.
- Set metrics can be null. Strength, cardio, and stair-machine exercises use
  different combinations of the available metrics.

## Pagination: fetch every page

Paginated endpoints take `page` (starting at 1) and `pageSize`, then return
`page` and `page_count`. Continue until `page >= page_count`, including the
last page. Do not infer completion from the returned array length.

| Collection | Response array | Maximum `pageSize` |
| --- | --- | ---: |
| Workouts | `workouts` | 10 |
| Routines | `routines` | 10 |
| Exercise templates | `exercise_templates` | 100 |
| Routine folders | `routine_folders` | 10 |
| Workout events | `events` | 10 |
| Body measurements | `body_measurements` | 10 |

```js
async function fetchEveryPage(path, collectionKey, pageSize) {
  const all = [];
  for (let page = 1; ; page += 1) {
    const url = new URL(path, process.env.HEVY_API_BASE_URL);
    url.searchParams.set('page', page);
    url.searchParams.set('pageSize', pageSize);
    const response = await fetch(url, {
      headers: { 'api-key': process.env.HEVY_API_KEY },
    });
    if (!response.ok) throw new Error(`Hevy ${response.status}: ${await response.text()}`);
    const body = await response.json();
    all.push(...body[collectionKey]);
    if (body.page >= body.page_count) return all;
  }
}

const templates = await fetchEveryPage('/v1/exercise_templates', 'exercise_templates', 100);
```

## Writes and failures

- Send `Content-Type: application/json` with every `POST` and `PUT`.
- Check the HTTP response before persisting local state.
- `400` means invalid input; capture the returned error safely without
  exposing the API key.
- Creating a body measurement for an existing date returns `409`.
- `PUT /v1/body_measurements/{date}` replaces all fields: omitted fields are
  set to `null`. Read the current measurement and send the full object when
  changing one value only.
- The snapshot does not document rate limits or retry policy. Use timeouts,
  exponential backoff for transient failures, and idempotency controls for
  writes in the application.
