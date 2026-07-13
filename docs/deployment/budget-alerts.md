# Budget Alerts

Budget alerts are required before cloud resources are deployed.

## Required Thresholds

- 50% of $300
- 90% of $300
- 100% of $300

## Verification

Use `deploy/scripts/win/validate-budget-alerts.ps1` or inspect Cloud Billing budgets in the Google Cloud Console.

The deployment should not proceed if these alerts are missing.
