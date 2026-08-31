# Hevy API integration

This directory is the local, implementation-oriented reference for connecting
Tuxedo Fitness to [Hevy](https://www.hevyapp.com/).

> This public API requires Hevy Pro. Hevy states that the API may change, so
> verify the current official documentation before a release and refresh the
> local snapshot when its contract changes.

## Start here

1. [01-access-and-conventions.md](01-access-and-conventions.md): API key,
   security, units, pagination, and error-handling conventions.
2. [02-data-model.md](02-data-model.md): catalogue, planned routines,
   completed workouts, sets, history, and measurements.
3. [03-integration-flows.md](03-integration-flows.md): initial import,
   incremental sync, and complete creation payloads.
4. [04-endpoints.md](04-endpoints.md): endpoint reference and read examples.

## Quick map

| Product need | Hevy resource | Main endpoint |
| --- | --- | --- |
| Identify the connected account | User | `GET /v1/user/info` |
| Fetch every available exercise | Exercise templates | `GET /v1/exercise_templates` |
| Create a custom exercise | Exercise templates | `POST /v1/exercise_templates` |
| Fetch the user's planned workouts | Routines | `GET /v1/routines` |
| Create or edit a planned workout | Routines | `POST`/`PUT /v1/routines` |
| Organise routines | Routine folders | `GET`/`POST /v1/routine_folders` |
| Fetch completed training sessions | Workouts | `GET /v1/workouts` |
| Record or edit a completed session | Workouts | `POST`/`PUT /v1/workouts` |
| Keep the workout cache current | Workout events | `GET /v1/workouts/events` |
| Analyse one exercise over time | Exercise history | `GET /v1/exercise_history/{exerciseTemplateId}` |
| Track body composition | Body measurements | `GET /v1/body_measurements` |

## Source material and boundaries

- The Markdown files in this directory are the project's maintained,
  implementation-oriented integration guide.
- The original Swagger capture is retained only in ignored private storage. It
  is not redistributed because the repository has no recorded permission to
  republish the provider's complete documentation bundle.
- Provenance, retrieval date, and the source hash used for the adapter baseline
  are recorded in [`../hevy-integration.md`](../hevy-integration.md).
- All example IDs and credentials are fictitious.

## Important limitations in this snapshot

- Authentication uses `api-key`, not `Authorization: Bearer ...`.
- Paginated responses expose `page` and `page_count`; always fetch every page.
- No `DELETE` endpoint is documented for workouts, routines, exercises, or
  measurements. Workout deletions are reported through the event feed.
- A **routine** is a reusable planned workout. A **workout** is a completed,
  time-bound training session. They have distinct payloads.
