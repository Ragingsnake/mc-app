# Monitoring Setup

## Install

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/kube-prometheus-values.yaml
```

## Access Grafana

```bash
# Port-forward (local dev)
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

# Or use the NodePort: http://localhost:32300
# Default credentials: admin / admin
```

## What is monitored

- All pods in `mc-app`, `mc-app-dev`, `mc-app-prod` namespaces with `prometheus.io/scrape: true` annotation
- Standard Kubernetes cluster metrics (node CPU, memory, pod restarts)
- HPA scaling events
