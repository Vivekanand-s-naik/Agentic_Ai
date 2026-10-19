# Kubernetes Best Practices

- Set resource requests and limits on every container
- Use readiness/liveness probes
- Run containers as non-root with read-only filesystem where possible
- Avoid `latest` image tags; use immutable tags/digests
- Use namespaces and RBAC for isolation
- Store secrets externally; never in git
- Monitor with Prometheus/Grafana; centralize logs
- Keep manifests in git; use GitOps
- Test manifests with kubeconform; lint with kube-linter
