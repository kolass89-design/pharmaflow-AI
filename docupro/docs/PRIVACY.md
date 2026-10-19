# Privacy

DOCUPRO is designed so that the operator of the service, and anyone who gains
access to its storage, learns as little as possible about users' documents.

## What is stored

| Data | Where | Lifetime |
| --- | --- | --- |
| Uploaded document | Server, `jobs/<id>/input`, mode 0700 | Deleted as soon as the conversion ends — success, failure or cancellation |
| Converted document | Server, `jobs/<id>/output` | Deleted 30 minutes after conversion, or 120 s after the last artifact is downloaded, or immediately when the user deletes it |
| Job metadata | Server memory | Until expiry, then removed by the sweeper (bounded to 200 records) |
| Request logs | Server stdout | Job ID, tool ID, duration, status code, error code. No filenames, no content, no tokens |
| History (optional) | User's browser `localStorage` | Until cleared by the user; contains tool, file names, sizes, timestamps and artifact links |
| Theme and preferences | User's browser `localStorage` | Until cleared |

Nothing is written to a database, a message queue or an external service.
There is no analytics, no telemetry and no third-party script.

## What is not done

* Documents are not used for model training.
* There is no account, so no email address, password or profile exists.
* There is no server-side history endpoint: `GET /api/jobs` returns counters
  only.
* Filenames never appear in server logs. A download URL contains a per-job
  token that is required to retrieve the artifact.

## Retention details

* `DOCUPRO_RETENTION_MINUTES` (30) — hard ceiling for every output.
* `DOCUPRO_DELETE_AFTER_DOWNLOAD_SECONDS` (120) — after all artifacts have been
  downloaded once, retention is shortened to this value. Set it to `0` to keep
  the full window.
* The sweeper runs every `DOCUPRO_SWEEP_SECONDS` (30); deletion therefore
  happens within half a minute of expiry.
* On restart, job directories older than 60 seconds that are not tracked in
  memory are removed.

## User controls

* The result screen shows a countdown and a **Delete now** button that removes
  the job and its files immediately.
* History can be disabled in Settings, and cleared at any time.
* Cancelling a conversion deletes the uploaded files and any partial output.

## Cookies

The application sets no cookies. Theme, preferences and history use
`localStorage`, which is never sent to the server.

## Data location

Everything stays on the host the operator deploys. There is no outbound network
call during conversion; DOCUPRO does not contact any third-party service.

## Children and sensitive documents

The service is not directed at children and is not a certified store for
regulated data. Operators handling health, financial or personal data should
add full-disk encryption, access controls at the proxy and a retention policy
that matches their jurisdiction.
