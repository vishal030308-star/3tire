Both are running perfectly! Here's your exact status:

- ✅ **Ollama 0.18.2** — running, llama3 downloaded and tested
- ✅ **Flowise 3.1.0** — running on `http://localhost:3000`
- ✅ **Node.js v20.20.1** — good version
- ✅ **WSL2** (Ubuntu on Windows) — your environment

Now let's build the agent. Here's your **Phase-by-phase execution plan** tailored to your exact setup.

---

## Step 1 — Pull the models you need

Open a **new WSL terminal** (keep Flowise running in the other one):

```bash
# Fast general model (already have llama3 - good!)
ollama pull mistral          # 4GB — faster responses
ollama pull codellama        # 4GB — for code/log analysis

# Verify all models
ollama list
```

---

## Step 2 — Install ChromaDB (vector store for your project docs)

```bash
# Install Python deps
pip install chromadb sentence-transformers --break-system-packages

# OR use Docker (recommended - cleaner)
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  chromadb/chroma:latest

# Verify it's running
curl http://localhost:8000/api/v1/heartbeat
```

---

## Step 3 — Install Prometheus + Grafana + Loki via Docker Compose

First check Docker is available in WSL:
```bash
docker --version
docker ps
```

If Docker works, create the monitoring stack:

```bash
mkdir ~/devops-ai && cd ~/devops-ai
```

Create `docker-compose.yml`:
```bash
cat > docker-compose.yml << 'EOF'
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_ALLOW_LOADING_UNSIGNED_PLUGINS=true
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    restart: unless-stopped

  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - /var/log:/var/log:ro
      - ./promtail.yml:/etc/promtail/config.yml
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    ports:
      - "8000:8000"
    volumes:
      - chroma-data:/chroma/chroma
    restart: unless-stopped

volumes:
  grafana-data:
  chroma-data:
EOF
```

Create `prometheus.yml`:
```bash
cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['host.docker.internal:9100']

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']
EOF
```

Create `promtail.yml`:
```bash
cat > promtail.yml << 'EOF'
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/*.log
EOF
```

Start everything:
```bash
docker compose up -d

# Verify all containers running
docker ps
```

---

## Step 4 — Build your Flowise agent (the actual AI brain)

Open your browser → `http://localhost:3000`

### 4a — Create a new Chatflow

Click **"Add New"** → name it `DevOps AI Assistant`

### 4b — Add these nodes (drag from left panel)

**Node 1: ChatOllama**
- Search "ChatOllama" in nodes panel
- Base URL: `http://localhost:11434`
- Model Name: `llama3`
- Temperature: `0.2` (lower = more factual for DevOps)

**Node 2: Ollama Embeddings**
- Search "OllamaEmbeddings"
- Base URL: `http://localhost:11434`
- Model: `nomic-embed-text` (pull it first: `ollama pull nomic-embed-text`)

**Node 3: Chroma Vector Store**
- Search "Chroma"
- Chroma URL: `http://localhost:8000`
- Collection Name: `devops-knowledge`
- Connect Ollama Embeddings → Chroma

**Node 4: Conversational Retrieval QA Chain**
- Search "Conversational Retrieval QA"
- Connect: ChatOllama → this node
- Connect: Chroma → this node (as retriever)

**Node 5: Buffer Memory**
- Search "Buffer Memory"
- Connect → Conversational Retrieval QA Chain

### 4c — Add a system prompt

Inside the Conversational Retrieval QA Chain node, set the system message:
```
You are a senior DevOps engineer AI assistant. You have full knowledge of:
- This project's codebase, architecture, and configuration files
- CI/CD pipeline structure and recent build logs
- Docker container status and logs
- Kubernetes pod events and metrics
- System resource usage (CPU, RAM, disk)
- Grafana dashboard metrics and alerts

When answering:
1. Be specific - reference actual container names, pod names, file paths
2. For errors, provide root cause analysis and fix commands
3. For metrics questions, explain what the numbers mean
4. Always suggest preventive measures after solving issues

Current environment: WSL2 on Windows, Ollama local LLM, Flowise orchestration.
```

**Save → click the green Play button → test it!**

---

## Step 5 — Feed your project knowledge

Open a new terminal:

```bash
cd ~/devops-ai

# Create a script to ingest your project into ChromaDB
cat > ingest.py << 'EOF'
import chromadb
import os

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_or_create_collection("devops-knowledge")

# Read your project files
project_path = "/mnt/c/Users/WaveAxis/Desktop/vishal/portfolio"
docs = []
ids = []
i = 0

for root, dirs, files in os.walk(project_path):
    # Skip node_modules, .git, etc
    dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'dist']]
    for file in files:
        if file.endswith(('.md', '.yml', '.yaml', '.json', '.txt', '.env.example', '.dockerfile', 'Dockerfile')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', errors='ignore') as f:
                    content = f.read()
                    if content.strip():
                        docs.append(content[:2000])  # chunk limit
                        ids.append(f"doc_{i}")
                        i += 1
                        print(f"Loaded: {filepath}")
            except Exception as e:
                print(f"Skipped {filepath}: {e}")

if docs:
    collection.add(documents=docs, ids=ids)
    print(f"\n✅ Ingested {len(docs)} documents into ChromaDB")
else:
    print("No documents found")
EOF

python3 ingest.py
```

---

## Step 6 — Connect Grafana

1. Open `http://localhost:3001` → login with `admin / admin123`
2. Go to **Connections → Add data source**
   - Add **Prometheus** → URL: `http://prometheus:9090`
   - Add **Loki** → URL: `http://loki:3100`
3. Import a K8s dashboard → **Dashboards → Import → ID: `315`** (Kubernetes cluster)
4. Import Node Exporter dashboard → **ID: `1860`**

**Add the AI chat panel to Grafana:**
- Add a new panel → type **Text**
- Set content to:
```html
<iframe 
  src="http://localhost:3000/chatbot/YOUR_CHATFLOW_ID" 
  width="100%" 
  height="600px" 
  frameborder="0"
  style="border-radius:8px">
</iframe>
```

Get your chatflow ID from Flowise → top-right menu → **"Embed"** → copy the ID from the URL.

---

## Step 7 — Final health check

```bash
# Run this anytime to check everything is up
echo "=== Ollama ===" && curl -s http://localhost:11434 | head -1
echo "=== Flowise ===" && curl -s http://localhost:3000/api/v1/ping
echo "=== ChromaDB ===" && curl -s http://localhost:8000/api/v1/heartbeat
echo "=== Prometheus ===" && curl -s http://localhost:9090/-/healthy
echo "=== Grafana ===" && curl -s http://localhost:3001/api/health
echo "=== Loki ===" && curl -s http://localhost:3100/ready
echo "=== Docker containers ===" && docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Your current status summary

| Component | Status | Action needed |
|-----------|--------|---------------|
| Ollama | ✅ Running | Pull `nomic-embed-text` |
| llama3 model | ✅ Downloaded | Ready |
| Flowise 3.1.0 | ✅ Running | Build chatflow |
| ChromaDB | ⬜ Not started | `docker compose up -d` |
| Prometheus | ⬜ Not started | `docker compose up -d` |
| Grafana | ⬜ Not started | `docker compose up -d` |
| Loki | ⬜ Not started | `docker compose up -d` |

**Your immediate next command:**
```bash
ollama pull nomic-embed-text
```
Then do the `docker compose up -d` from Step 3. Come back here when you hit any error and paste the output — I'll debug it with you!
