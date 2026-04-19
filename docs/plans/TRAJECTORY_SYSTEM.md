# Trajectory System Implementation Plan

## 1. Database & Models
- Update `User` model in `backend/app/models.py`:
  - Add `trajectory_update_day` (int, default 6 for Sunday).
  - Add `next_trajectory_date` (datetime, nullable).
- Create `Trajectory` model:
  - `id` (UUID), `user_id` (FK to User), `original_goal` (String), `rephrased_question` (String), `is_active` (Boolean), `created_at` (Datetime).
- Create `CheckinTrajectoryResponse` model (or add JSON field to Checkin):
  - Let's use a relational model: `id` (UUID), `checkin_id` (FK), `trajectory_goal_id` (FK), `completed` (Boolean).
- Update schemas (e.g. `UserPublic`, `CheckinCreate`).
- Generate Alembic migration and apply.

## 2. AI Integration
- Update `backend/app/koios_client/KoiosClient.py`:
  - Add `rephrase_trajectory_goal(user_id, goal)` method. This runs ONLY when a new trajectory is created or updated, storing the rephrased question in the DB.
  - Prompt: "Rephrase this goal into a short yes/no question starting with 'Did you...' or 'Were you...'."
  - Add `brainstorm_trajectory(user_id, message, history)` method. This handles the mini-chat for the user to brainstorm trajectory ideas.

## 3. Backend Routes
- Create `backend/app/api/routes/trajectories.py`:
  - `GET /trajectories/active`
  - `POST /trajectories/` (Takes original text, calls Koios for rephrase, saves to DB. Only calls rephrase for new/changed trajectories)
  - `PATCH /trajectories/{id}` (To toggle `is_active` or update text)
  - `DELETE /trajectories/{id}`
  - `POST /trajectories/brainstorm` (Endpoint for the mini-chat to bounce ideas off Koios)
- Update `checkins.py` and `backend/app/checkin/Checkin.py`:
  - Accept `trajectory_responses` in `CheckinCreate`.
  - Save responses and adjust `alignment_score` calculation to include completed trajectories.
- Update `users.py`:
  - Allow updating `trajectory_update_day`.
  - Calculate and set `next_trajectory_date` when onboarding is completed or when the user submits the Trajectory modal.

## 4. Frontend Client
- Run `./scripts/generate-client.sh` to update OpenAPI types.

## 5. Frontend UI
- **Settings:** Add "Trajectory Update Day" dropdown in `UserSettings`.
- **TrajectoryModal:**
  - Create `frontend/src/components/Trajectories/TrajectoryModal.tsx`.
  - Shows list of active/past goals, allows adding new ones (with loading state for AI rephrase), and deleting/deactivating.
  - Add an "Ask Koios?" button that opens a mini chat interface within or alongside the modal. This allows the user to brainstorm ideas before creating the trajectory.
- **Check-in Update:**
  - Modify `AutoCheckinModal.tsx` to query active trajectory goals.
  - Display them as checkboxes (e.g. `[ ] Did you work out for 30 mins?`).
  - Submit responses to the check-in endpoint.
- **Trigger Logic:**
  - In `index.tsx` or main layout, check if onboarding is complete.
  - If `next_trajectory_date` is null (first time) or <= today, show `TrajectoryModal`.
  - Ensure it blocks the daily check-in until completed.
