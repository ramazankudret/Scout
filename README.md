# Scout - AI Cyber Security Agent

🛡️ **Scout** - Otonom siber güvenlik ajanı. Ağınızı izler, tehditleri tespit eder ve otomatik aksiyon alır.

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Docker & Docker Compose
- Python 3.11+ (geliştirme için)
- Node.js 20+ (frontend için)

### Docker ile Çalıştırma (Önerilen)
```bash
# Tüm servisleri başlat
docker-compose -f docker/docker-compose.yml up -d

# Logları izle
docker-compose -f docker/docker-compose.yml logs -f

# Durdur
docker-compose -f docker/docker-compose.yml down
```

### Ollama Kurulumu (Local LLM)

Scout, yerel yapay zeka analizi için Ollama kullanır. API masrafı olmadan, gizliliğinizi koruyarak çalışır.

```bash
# 1. Ollama'yı indir ve kur
# Windows: https://ollama.com/download/windows
# Linux: curl -fsSL https://ollama.com/install.sh | sh
# macOS: brew install ollama

# 2. Ollama servisini başlat
ollama serve

# 3. Model indir (önerilen: llama3.1:8b - RTX 4060 8GB için ideal)
ollama pull llama3.1:8b

# Alternatif modeller:
# ollama pull deepseek-r1:8b    # Reasoning odaklı
# ollama pull mistral:7b         # Hızlı ve hafif
# ollama pull codellama:7b       # Kod analizi için
```

**Model Seçimi (.env dosyasında):**
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### Local Geliştirme

#### Backend
```bash
cd backend

# Poetry kurulumu (ilk seferinde)
pip install poetry

# Bağımlılıkları yükle
poetry install

# .env dosyasını oluştur
cp .env.example .env

# Sunucuyu başlat
poetry run uvicorn src.scout.main:app --reload
```

API dokümantasyonu: http://localhost:8000/docs

#### LLM Test Endpoint'leri
```bash
# LLM sağlık kontrolü
curl http://localhost:8000/api/v1/llm/health

# Basit sohbet
curl -X POST http://localhost:8000/api/v1/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the signs of a brute force attack?"}'

# Log analizi
curl -X POST http://localhost:8000/api/v1/llm/analyze/logs \
  -H "Content-Type: application/json" \
  -d '{"logs": "Failed login from 192.168.1.100 x 50 times", "query": "Find suspicious activity"}'

# Tehdit analizi
curl -X POST http://localhost:8000/api/v1/llm/analyze/threat \
  -H "Content-Type: application/json" \
  -d '{"threat_data": {"source_ip": "10.0.0.5", "event": "port_scan", "ports": [22,80,443]}}'
```

#### Frontend
```bash
cd frontend

# Bağımlılıkları yükle
npm install

# Geliştirme sunucusunu başlat
npm run dev
```

Dashboard: http://localhost:3000

## 📁 Proje Yapısı

```
Scout/
├── backend/               # Python FastAPI Backend
│   ├── src/scout/
│   │   ├── core/          # Config, Logging, Exceptions
│   │   ├── domain/        # Entities, Events, Interfaces (DDD)
│   │   ├── application/   # Use Cases, Services
│   │   ├── infrastructure/# API, DB, LLM Adapters
│   │   └── modules/       # Güvenlik Modülleri (Plugin Sistemi)
│   │       ├── stealth/   # Pasif gözlem modu
│   │       ├── defense/   # Aktif koruma modu
│   │       └── hunter/    # Proaktif tarama modu
│   └── tests/
├── frontend/              # Next.js Dashboard
├── docker/                # Docker konfigürasyonları
└── docs/                  # Dokümantasyon
```

## 🧩 Modül Sistemi

Scout, plugin tabanlı bir mimari kullanır. Yeni modül eklemek için:

```python
from scout.modules import BaseModule, ExecutionContext, ModuleResult

class MySecurityModule(BaseModule):
    name = "my_module"
    description = "Benim güvenlik modülüm"
    version = "1.0.0"

    async def execute(self, context: ExecutionContext) -> ModuleResult:
        # Modül mantığı
        return ModuleResult(success=True, data={...})
```

## 🧪 Testler

```bash
cd backend

# Tüm testler
poetry run pytest

# Sadece unit testler (hızlı)
poetry run pytest tests/unit

# Coverage raporu
poetry run pytest --cov=src/scout
```

## 📜 Lisans

Proprietary - Tüm hakları saklıdır.
