# Release State

Each deployed release is identified by a Git commit SHA.

## Release Record

```json
{
  "environment": "staging",
  "commitSha": "abc123",
  "deployedAt": "2026-07-12T00:00:00Z",
  "images": {
    "frontend": "asia-southeast1-docker.pkg.dev/project/repo/frontend:abc123"
  },
  "smokeStatus": "passed",
  "knownGood": true
}
```

## Rules

- Mark `knownGood=true` only after smoke checks pass.
- Rollback targets the previous known-good SHA.
- Do not retag or deploy `latest`.
