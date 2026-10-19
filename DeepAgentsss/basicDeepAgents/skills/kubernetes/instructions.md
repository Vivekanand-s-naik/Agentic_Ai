# Kubernetes Instructions

## Manifests
- Always set resource requests/limits
- Use liveness/readiness probes
- Run as non-root; drop capabilities
- Use namespaces for isolation

## Deployment
- Rolling updates with maxUnavailable/maxSurge
- Use Helm charts or Kustomize for templating
- GitOps (ArgoCD/Flux) for production

## Debugging
- `kubectl describe`, `kubectl logs`, `kubectl get events`
- Check node pressure, pod scheduling, image pull errors
- Use `kubectl debug` for ephemeral containers

## Security
- RBAC least privilege; avoid cluster-admin for apps
- NetworkPolicies to restrict pod-to-pod traffic
- Secrets via external secrets operator / sealed secrets
