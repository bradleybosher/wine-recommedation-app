# routes/insights.py

## Responsibility

Exposes `GET /profile/insights` — returns palate drift suggestions derived from the active profile's flight history.

## Endpoint

**`GET /profile/insights`** → `list[PalateDriftSuggestion]`

Requires Bearer JWT + `X-Profile-Id` header.

Delegates entirely to `insights.compute_drift_suggestions(profile.id)`. Returns an empty list `[]` when there are insufficient flights or no pattern is found — never 404.

## Authentication

Standard `Depends(get_current_profile)` — same as all other profile-scoped endpoints. The profile ID comes from the `X-Profile-Id` header validated against the JWT user.

## Response Shape

```json
[
  {
    "dimension": "preferred_grapes",
    "current": ["Pinot Noir", "Nebbiolo"],
    "suggested": ["Sangiovese"],
    "rationale": "'Sangiovese' appeared in 7 of your last 20 recommendation flights but isn't in your stated preferred grapes.",
    "supportingFlightIds": ["abc123", "def456"]
  }
]
```

Field names are camelCase in JSON (auto-aliased via `to_camel`).
