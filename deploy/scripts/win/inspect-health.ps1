param(
    [string]$Namespace = "helmet-staging"
)

$ErrorActionPreference = "Stop"
kubectl -n $Namespace get pods -o wide
kubectl -n $Namespace get svc
kubectl -n $Namespace get ingressroute 2>$null
kubectl -n $Namespace get certificates 2>$null
kubectl -n $Namespace get events --sort-by=.lastTimestamp
kubectl -n $Namespace get deploy -o jsonpath="{range .items[*]}{.metadata.name}{': '}{range .spec.template.spec.containers[*]}{.image}{' '}{end}{'\n'}{end}"
