# Minecraft Story Generator (Microservices Simulation)

An event-driven, text-based multiplayer Minecraft adventure simulator built on a highly decoupled microservices architecture. The application simulates virtual players joining a server, generating relationships, encountering environmental challenges, battling legendary bosses, and working toward epic endings.

---

## Architecture Diagram

The application consists of a React frontend and 8 distinct backend microservices communicating asynchronously using **Redis Streams** as the message broker, with caching layered in **Redis Cache** and persistent storage handled by **PostgreSQL** (packaged via Helm). Secrets are dynamically retrieved from **HashiCorp Vault** using the **External Secrets Operator (ESO)**.

```mermaid
graph TD
    UI[React Frontend] <-->|HTTP REST /api/...| AG[API Gateway]
    AG <-->|HTTP REST /generate| SO[Story Orchestrator]
    
    subgraph Event-Driven Generator Pipeline
        SO -->|Publish init| S_Char([Stream: character request])
        S_Char --> CG[character-gen]
        CG -->|Publish| S_Scen([Stream: scenario request])
        
        S_Scen --> SG[scenario-gen]
        SG -->|Publish| S_Batt([Stream: battle request])
        
        S_Batt --> BG[battle-gen]
        BG -->|Loop back| S_Scen
        BG -->|Publish end| S_End([Stream: ending request])
        
        S_End --> EG[endings-gen]
        EG -->|Publish db write| S_DB([Stream: db request])
        
        S_DB --> DB[story-db-service]
    end

    DB -->|Read/Write| Postgres[(PostgreSQL DB)]
    DB -->|Cache final story| RC[(Redis Cache)]
    SO <-->|Poll status| RC
    
    %% Vault integration
    Vault[(HashiCorp Vault)] -->|Sync Secrets| ESO[External Secrets Operator] -->|Inject Secret| DB
```

---

## System Services

### Core Frontend & Routing
*   **Frontend (React + Vite):** Serves the user interface. It renders the narrative with a typewriter effect, maintains a scrolling game chat pane, displays live player badges (health, location, inventory), and allows rating/commenting on saved stories.
*   **API Gateway (Flask, Port 5000):** The single ingress point. It forwards requests to the Orchestrator, manages story publishing, and caches the database directory lists (`all_stories`) inside Redis for 60 seconds.
*   **Story Orchestrator (Flask, Port 5015):** Starts the generation cycle. It creates a unique UUID `correlation_id`, publishes the initial state payload to `stream:character:request`, and polls Redis Cache (`story:<correlation_id>`) to return results to the polling frontend.

### The Pipeline Generator Microservices
*   **Character Gen (Flask, Port 5011):** Spawns 3 to 5 players with gamer tags (e.g. `xX_NoobSlayer_Xx`, `GamerNoob`, `RedstoneGod`), assigns health (20 HP), picks locations, defines personalities, and sets random initial relationship scores.
*   **Scenario Gen (Flask, Port 5012):** Tracks time of day (Morning $\rightarrow$ Afternoon $\rightarrow$ Night). Triggers event scenarios such as wrong tool arguments, base sabotage, reputation-based theft, or map exploration (e.g. desert temple) depending on the group's current inventory.
*   **Battle Gen (Flask, Port 5013):** Executes combat logic. If a threat (e.g. Herobrine, Wither, or Charged Creeper) is spawned, it calculates damage, processes teammate ditching (which harms relationships), handles death drops, and evaluates player retaliation. If no threat is present, it processes environmental accidents (like falling in lava).
*   **Endings Gen (Flask, Port 5014):** Concludes the adventure. If all players are dead, it triggers a game over. If they reach 10 rounds, it writes a victory ending (e.g. slaying the Ender Dragon). It then compiles the separate event snippets into a single continuous, readable markdown transcript.

### Database & Security
*   **Story DB Service (Flask, Port 5002):** Connects to the database (SQLite for local runs, PostgreSQL in production). It listens for completed stories on `stream:db:request` to cache them in Redis and provides endpoints to comment and rate published stories.
*   **HashiCorp Vault & ESO:** High-value database credentials are stored securely in Vault. The External Secrets Operator retrieves these secrets and mounts them as native Kubernetes Secrets, which are then injected as environment variables in the deployment container.

---

## CI/CD Pipeline

### Overview

The project uses a **GitOps** workflow powered by Gitea Actions (CI) and **ArgoCD** (CD).

```mermaid
graph LR
    DEV[Developer Push] --> CI[Gitea CI - ci-auto.yaml]
    CI --> LINT[Lint + Security Scan]
    LINT --> BUILD[Build & Push to DockerHub]
    BUILD --> TAG[Update image tag in values.yaml]
    TAG --> GITPUSH[Git push back to repo]
    GITPUSH --> ARGO[ArgoCD detects change]
    ARGO --> DEP_DEV[Deploy to mc-app-dev]
    ARGO --> DEP_PROD[Deploy to mc-app-prod]
```

### CI Pipeline (`ci-auto.yaml`)

The CI pipeline is **smart**: it only builds the microservice(s) that actually changed using `dorny/paths-filter`. For each changed service, it:

1. **Lints** the code (ESLint/oxlint for frontend, `py_compile` for Python services)
2. **Scans** with Trivy for CRITICAL/HIGH CVEs
3. **Builds & Pushes** the Docker image to `ragingsnake/mc-app:<service>-<git-sha>` on DockerHub
4. **Updates** the image tag in `helm/minecraft-story-app/values.yaml` and commits it back to the repo

### ArgoCD Setup

ArgoCD watches the `helm/minecraft-story-app` directory. When the CI pipeline commits a new image tag, ArgoCD automatically syncs and rolls out the updated deployment.

**Install ArgoCD:**
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Apply Application manifests:**
```bash
kubectl apply -f argocd/application-dev.yaml
kubectl apply -f argocd/application-prod.yaml
```

---

## Monitoring (Prometheus + Grafana)

The app uses the `kube-prometheus-stack` Helm chart. All microservice pods are annotated with `prometheus.io/scrape: "true"` for automatic metric discovery.

**Install:**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/kube-prometheus-values.yaml
```

**Access Grafana:** `http://localhost:32300` (NodePort) — default credentials: `admin / admin`

---

## Autoscaling (HPA)

Horizontal Pod Autoscalers are configured via the Helm chart for CPU-based scaling:

| Service | Dev Min/Max | Prod Min/Max | CPU Target |
|---|---|---|---|
| api-gateway | 1 / 3 | 2 / 8 | 55–70% |
| story-orchestrator | 1 / 3 | 2 / 8 | 55–70% |
| scenario-gen | 1 / 4 | 2 / 10 | 55–70% |
| battle-gen | 1 / 4 | 2 / 10 | 55–70% |
| character-gen | 1 / 3 | 2 / 6 | 60–80% |

Scaling is environment-specific via `values-dev.yaml` and `values-prod.yaml`.