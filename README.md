Scout - AI Cyber Security Agent
🛡️ Scout is an autonomous cybersecurity agent designed to monitor network traffic, detect advanced threats, and take automated defensive actions using state-of-the-art AI.

🚀 Quick Start
Prerequisites
Docker & Docker Compose

Python 3.11+ (for development)

Node.js 20+ (for frontend dashboard)

Run with Docker (Recommended)
Bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Follow logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
🧠 LLM Orchestration
Scout features a hybrid LLM architecture, allowing users to choose between local privacy and high-performance cloud reasoning.

Local LLM (via Ollama)
Scout uses Ollama for local AI analysis, ensuring data privacy with zero API costs.

Install Ollama: Download here

Start Service: ollama serve

Pull Recommended Model:

Bash
# Optimized for mid-range GPUs (like RTX 4060 8GB)
ollama pull llama3.1:8b

# Alternatives:
# ollama pull deepseek-r1:8b    (Reasoning-focused)
# ollama pull codellama:7b      (Security code analysis)
☁️ Cloud LLM Support (Experimental)
We are currently integrating Claude 3.5 Sonnet (via Anthropic API) for complex network forensic analysis.

Claude Integration: Utilizing MCP (Model Context Protocol) to provide Claude with direct context from network logs.

Enterprise Reasoning: Leveraging Claude's 200k+ context window for deep-dive incident response.

Configuration (.env):

Bash
LLM_PROVIDER=ollama # or 'anthropic'
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
ANTHROPIC_API_KEY=your_key_here
🛠️ Local Development
Backend (FastAPI)
Bash
cd backend
pip install poetry
poetry install
cp .env.example .env
poetry run uvicorn src.scout.main:app --reload
API Documentation: http://localhost:8000/docs

Frontend (Next.js)
Bash
cd frontend
npm install
npm run dev
Dashboard: http://localhost:3000

📁 Project Architecture
Plaintext
Scout/
├── backend/                # Python FastAPI Backend
│   ├── src/scout/
│   │   ├── core/           # Config, Logging, Exceptions
│   │   ├── domain/         # Entities, Events, Interfaces (DDD)
│   │   ├── application/    # Use Cases, Services
│   │   ├── infrastructure/ # API, DB, LLM Adapters (Claude/Ollama)
│   │   └── modules/        # Security Plugins
│   │       ├── stealth/    # Passive Observation
│   │       ├── defense/    # Active Protection
│   │       └── hunter/     # Proactive Scanning
│   └── tests/
├── frontend/               # Next.js Dashboard
├── docker/                 # Container Configurations
└── docs/                   # Technical Documentation
🧩 Plugin System
Scout is built with a modular architecture. You can easily extend its capabilities:

Python
from scout.modules import BaseModule, ExecutionContext, ModuleResult

class MySecurityModule(BaseModule):
    name = "custom_scanner"
    description = "AI-powered vulnerability scanner"
    version = "1.0.0"

    async def execute(self, context: ExecutionContext) -> ModuleResult:
        # Module logic here
        return ModuleResult(success=True, data={"status": "secure"})
🧪 Testing & Quality
Bash
cd backend
poetry run pytest                # Run all tests
poetry run pytest tests/unit     # Fast unit tests
poetry run pytest --cov=src/scout # Coverage report
📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
