# 📋 Todo App — Projet DevOps

Application de gestion de tâches déployée dans un environnement de production Kubernetes, suivant les bonnes pratiques DevOps.

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend   │────▶│ PostgreSQL  │
│ React+Nginx  │     │   FastAPI   │     │     DB      │
│   (port 80)  │     │ (port 8000) │     │ (port 5432) │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 📁 Structure du projet

```
projet-devops/
├── app/
│   ├── frontend/          # React + Dockerfile
│   ├── backend/           # FastAPI + Dockerfile
│   └── docker-compose.yml # Environnement staging
├── infra/
│   ├── ansible/           # Playbooks IaC
│   └── k8s/               # Manifests Kubernetes
├── .github/workflows/     # Pipeline CI/CD
├── monitoring/            # Config Prometheus/Grafana
└── docs/                  # Documentation projet
```

## 🚀 Quick Start (Local/Staging)

```bash
cd app/
docker-compose up --build
```
L'app est accessible sur `http://localhost`.

## ☸️ Déploiement Production (K3s)

### Prérequis
- 2 VMs Ubuntu (OVH Cloud)
- Ansible installé localement

### Installation du cluster
```bash
cd infra/ansible
# Éditer inventories/hosts.ini avec vos IPs
ansible-playbook -i inventories/hosts.ini setup-cluster.yml
```

### Déploiement de l'app
```bash
kubectl apply -f infra/k8s/namespace.yml
kubectl apply -f infra/k8s/postgres.yml
kubectl apply -f infra/k8s/backend.yml
kubectl apply -f infra/k8s/frontend.yml
```

### Monitoring
```bash
kubectl apply -f infra/k8s/monitoring.yml
kubectl apply -f infra/k8s/logging.yml
```
- Grafana : `http://<MASTER_IP>:30030` (admin/admin)
- Prometheus : `http://<MASTER_IP>:30090`

## 🔄 CI/CD

Pipeline GitHub Actions automatique sur push `main` :
1. Lint + Tests
2. Build images Docker
3. Push Docker Hub
4. Deploy sur K3s via SSH

### Secrets GitHub à configurer
- `DOCKER_HUB_USERNAME` / `DOCKER_HUB_TOKEN`
- `PROD_SERVER_IP` / `PROD_SERVER_USER` / `PROD_SSH_KEY`

## ✅ Pratiques DevOps implémentées

| Pratique | Outil |
|---|---|
| Conteneurisation | Docker |
| Orchestration | K3s (Kubernetes léger) |
| IaC | Ansible |
| CI/CD | GitHub Actions |
| Zero-downtime | Rolling Updates + Health Checks |
| Auto-scaling | HorizontalPodAutoscaler |
| Monitoring | Prometheus + Grafana + cAdvisor |
| Logging | Loki + Promtail |
| Versioning | Git (mono-repo) |

## 👥 Équipe

- **Personne A** : Dev + CI/CD
- **Personne B** : Ops + Infra
