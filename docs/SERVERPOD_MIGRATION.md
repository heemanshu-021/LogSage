# LogSage Serverpod Cloud migration

## Goal

Move LogSage to Flutter and Serverpod Cloud while preserving the Logfit-trained block anomaly detector and the current React/FastAPI implementation during the migration. Deployment is intentionally deferred until the user asks for it.

## Current state

- The existing product remains React/Vite + FastAPI/Python. Its trained Isolation Forest artifacts are local and Git-ignored under `ml/models/saved/`.
- A separate Serverpod 4.1.2 full-stack workspace now exists at `logsage_cloud/`, with a Flutter web client, generated Serverpod client, Serverpod backend, email identity-provider sign-in, and an initial PostgreSQL migration.
- Flutter 3.50.0 and Dart 3.14.0 are installed outside the repository. The checkout is based on `695145b2cb6f356f05147dbea017917f5d13113e`; changes remain uncommitted.
- The selected HackBriven × Serverpod challenge is **Here, together**. LogSage now has authenticated incident rooms with join codes, Postgres persistence for rooms, participants, and messages, and Serverpod live streams for updates.
- The existing Triage page has a metadata-free link to the room app. Responders enter the incident ID and title in the room form; the link does not send incident data to a configurable URL.
- Docker and Nginx are not part of this deployment path. Unused Docker files from the Serverpod template were removed.

## Platform and model constraint

Serverpod Cloud deploys Serverpod/Dart applications and can serve Flutter web from the Serverpod web server. It is not a Python runtime, so preserving the current Drain3 + fitted feature extractor + scikit-learn model requires a separate Python-capable inference service unless the complete parsing and scoring path is ported and validated in Dart. The `.joblib` artifact cannot be loaded directly by Serverpod. See the [Serverpod Cloud overview](https://docs.serverpod.dev/cloud), [Flutter web guide](https://docs.serverpod.dev/concepts/web-server/flutter-web), and [deployment guide](https://docs.serverpod.dev/deployments/deploy-to-serverpod-cloud).

## Challenge implementation

- Create an authenticated room for an incident. Serverpod generates a ten-character code for teammates.
- Teammates sign in, join by code, and see the room roster and persisted notes.
- Serverpod stream methods broadcast new notes and participant arrivals to clients watching that room.
- Flutter web uses HttpOnly cookie auth; local development uses `secure: false` only on localhost. Production requires HTTPS and the exact `SERVERPOD_ALLOWED_ORIGINS` value.
- The Triage page opens the room app without forwarding incident IDs or titles. Room creation currently uses manual entry; connecting it directly to the existing incident record is part of the broader data migration.

## Verification completed

- Serverpod protocol generation completed.
- Initial migration created for auth and incident-room tables.
- `flutter pub get` completed for the workspace.
- `dart analyze`: **no issues found**.
- `flutter build web --base-href /`: **passed**.
- `dart test test/integration/incident_room_endpoint_test.dart`: **2 passed**. The tests check authenticated membership, persisted messages, live updates, and rejection of an unjoined user.
- Existing React/Vite `npm run build` and `npm run lint`: **passed** after adding the metadata-free entry link.
- No Cloud deployment has been attempted.

## Remaining work

1. Run the Serverpod app locally and verify account registration/sign-in and the room UI across two browser sessions.
2. Migrate dashboard, incident list/detail/status, runbook search, and log upload/analyze into Flutter and Serverpod/Postgres.
3. Add a private inference service contract and verify held-out Logfit feature-vector, score, and prediction parity.
4. Finish auth, database migration, and real inference checks before requesting deployment setup.
5. When the user asks to deploy, configure the Cloud project, database, secrets, private inference URL, and allowed web origin, then verify the deployed flows.
