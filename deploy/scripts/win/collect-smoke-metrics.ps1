param(
    [string]$Namespace = "helmet-staging"
)

$ErrorActionPreference = "Stop"
kubectl -n $Namespace top pods 2>$null
kubectl -n $Namespace get pods -o jsonpath="{range .items[*]}{.metadata.name}{','}{range .status.containerStatuses[*]}{.restartCount}{' '}{end}{'\n'}{end}"
kubectl -n $Namespace logs deployment/inference-worker --tail=100 2>$null
