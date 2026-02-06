# Scout — Proje Analiz Raporu

**Tarih:** 2026-02-06  
**Analiz kapsamı:** Backend, Frontend, Veritabanı, Altyapı, Güvenlik, Kod kalitesi

---

## 1. Proje Özeti

**Scout**, Python (FastAPI) backend ve Next.js frontend kullanan, yerel LLM (Ollama) ile çalışan otonom bir siber güvenlik ajanıdır. Hem Red Team (saldırı simülasyonu, zafiyet tarama) hem Blue Team (savunma, izleme, tehdit analizi) işlevleri sunar.

### Temel Teknoloji Yığını

| Katman | Teknoloji | Versiyon |
|--------|-----------|----------|
| Backend | Python, FastAPI (async) | 3.11+, ^0.115 |
| ORM | SQLAlchemy (async) + Alembic | ^2.0 |
| Veritabanı | PostgreSQL + pgvector | — |
| LLM | LangChain + Ollama (yerel) | ^0.3 |
| Ajan Grafiği | LangGraph | ^0.2 |
| Frontend | Next.js (App Router), React | ^16.1.6, ^19.2 |
| UI | Tailwind CSS, Radix UI, Recharts | ^3.3, — |
| 3D Vizualizasyon | Three.js, React Three Fiber | ^0.182 |
| Container | Docker Compose | — |

---

## 2. Kod Tabanı Metrikleri

| Kategori | Dosya Sayısı | Satır Sayısı |
|----------|-------------|-------------|
| Backend Python (src) | 109 | ~13.865 |
| Backend Testler | 6 | ~443 |
| Frontend TS/TSX | 37 | ~5.134 |
| SQL Şema | 1 | ~765 |
| **Toplam** | **153** | **~20.207** |

### Backend Katman Dağılımı (satır)

| Katman | Satır |
|--------|-------|
| Infrastructure (API, DB, LLM, repos) | ~6.500 |
| Modules (Hunter, Stealth, Defense, vb.) | ~1.307 |
| Domain (entities, events, interfaces) | ~1.279 |
| Application (services, DTO) | ~1.195 |
| Core (config, graph, exceptions, vb.) | ~1.099 |
| Agents (Orchestrator, Supervisor, Learning) | ~914 |
| Tools (Nmap, Wireshark, Masscan, vb.) | ~345 |
| Guards (LLM Guard) | ~206 |

---

## 3. Mimari Analiz

### 3.1. Genel Mimari

Proje **Clean Architecture / DDD** prensiplerine uygun tasarlanmış:

```
Domain (entities, interfaces) ← Application (services) ← Infrastructure (API, DB, LLM)
```

- **Domain katmanı** altyapıya bağımlı değil; repository'ler port/interface olarak tanımlı (`IThreatRepository`, `ISupervisorRepository`, `ILearningRepository`).
- **Application katmanı** iş mantığını (ActionExecutor, ApprovalService, TimeoutService) içerir.
- **Infrastructure katmanı** dış dünyayla iletişimi sağlar (FastAPI route'lar, SQLAlchemy, Ollama).

**Değerlendirme:** ✅ Mimari yapı sağlam ve katmanlı. DDD prensipleri tutarlı uygulanmış.

### 3.2. Ajan Sistemi (LangGraph)

```
Orchestrator ──→ Hunter (proaktif tarama)
     │──→ Stealth (pasif izleme)
     └──→ Router Loop ──→ Defense (savunma)
```

- **Orchestrator:** Kullanıcı isteğini LLM (fast model) ile analiz eder, uygun ajana yönlendirir. Keyword-based fallback mevcur.
- **Hunter/Stealth/Defense:** Şu an kısmen mock; gerçek araç entegrasyonu (Nmap, tshark) planlanıyor.
- **Supervisor:** Ajan sağlığı, heartbeat, otomatik restart (simülasyon), HITL eskalasyonu.
- **Learning Engine:** Başarısız aksiyonları LLM ile analiz eder, ders çıkarır, DB + cache tutar.

**Değerlendirme:** ⚠️ Ajan altyapısı iyi tasarlanmış, ancak Hunter/Stealth/Defense ajanları henüz mock veri dönüyor. Supervisor restart mantığı simülasyon seviyesinde.

### 3.3. Modül Sistemi (Plugin)

- `BaseModule` → `execute()`, `start()`, `stop()` lifecycle
- `ModuleRegistry` → Singleton; modül kayıt, execute, execute_all
- Modlar: PASSIVE, ACTIVE, SIMULATION

**Mevcut modüller:**
| Modül | Durum | Açıklama |
|-------|-------|----------|
| Hunter | Kısmi | Nmap tool wrapper mevcut, DB yazma var |
| Stealth | Kısmi | tshark wrapper mevcut, trafik analizi |
| Defense | Kısmi | IP engelleme, HITL onay akışı |
| AI Pentest | Stub | Kalem test tarayıcısı iskeleti |
| Endpoint Security | Stub | Endpoint güvenlik tarayıcısı iskeleti |

**Değerlendirme:** ✅ Plugin mimarisi iyi. ⚠️ AI Pentest ve Endpoint Security modülleri henüz iskelet.

### 3.4. Tool Registry

Açık kaynak araçlar için wrapper'lar (`backend/src/scout/tools/`):

| Araç | Dosya | Durum |
|------|-------|-------|
| Nmap | nmap.py | Tamamlanmış (async subprocess) |
| Wireshark/tshark | wireshark.py | Tamamlanmış (async subprocess) |
| Masscan | masscan.py | Tamamlanmış (async subprocess) |
| Netdiscover | netdiscover.py | Tamamlanmış (async subprocess) |

**Değerlendirme:** ✅ Tool altyapısı hazır; LangChain tool binding interface'i mevcut.

---

## 4. Frontend Analiz

### 4.1. Sayfa Yapısı

| Sayfa | Yol | Durum |
|-------|-----|-------|
| Login / Register | `/login`, `/register` | ✅ Tamamlanmış |
| Dashboard (Ana) | `/dashboard` | ✅ KPI kartları, VectorSpace, Recent Activity |
| Assets | `/dashboard/assets` | ✅ CRUD |
| Incidents | `/dashboard/incidents` | ✅ CRUD |
| Approvals | `/dashboard/approvals` | ✅ HITL onay akışı |
| Supervisor | `/dashboard/supervisor` | ✅ Ajan durumu, restart, olaylar |
| Hunter | `/dashboard/hunter` | ✅ Tarama arayüzü |
| Stealth | `/dashboard/stealth` | ✅ İzleme arayüzü |
| Defense | `/dashboard/defense` | ⚠️ Kısmi |
| Pipeline | `/dashboard/pipeline` | ✅ Ajan akış görselleştirmesi |
| AI Security | `/dashboard/ai-security` | ⚠️ Mock veri |
| Scans | `/dashboard/scans` | ✅ Tarama geçmişi |
| Traffic | `/dashboard/traffic` | ✅ Trafik izleme |
| Charts | `/dashboard/charts` | ✅ Grafik |
| Settings | `/dashboard/settings` | ✅ Ayarlar |
| Users | `/dashboard/users` | ✅ Kullanıcı yönetimi |
| Notifications | `/dashboard/notifications` | ✅ Bildirimler |
| Security | `/dashboard/security` | ⚠️ Kısmi |
| Agents | `/dashboard/agents` | ✅ Ajan monitör |
| Chat (LLM) | Planlanıyor | ❌ Henüz yok |
| Agent Chat | Planlanıyor | ❌ Henüz yok |

### 4.2. Bileşenler

- **VectorSpace:** 3D görselleştirme (Three.js) — asset/node gösterimi. Şu an kısmen gerçek veri ile çalışıyor.
- **PipelineViz:** Ajan akış diyagramı (Orchestrator → Hunter/Stealth/Defense).
- **Sidebar:** Navigasyon menüsü (Command Center, Operations, Intelligence, System grupları).
- **ProtectedRoute:** Auth koruması (token kontrolü).
- **QueryProvider:** TanStack React Query provider.

**Değerlendirme:** ✅ Frontend kapsamlı ve iyi organize. ⚠️ Bazı sayfalar mock veri ile çalışıyor. Chat arayüzü henüz eklenmemiş.

---

## 5. Veritabanı Analiz

- **PostgreSQL + pgvector** (semantik arama desteği)
- **ORM:** SQLAlchemy (async) ile 15+ tablo
- **Temel tablolar:** User, Asset, Incident, Threat, ScanResult, LearnedLesson, SupervisorState, PendingAction, ApprovalPolicy, TrafficLog, ApiKey, vb.
- **Schema:** `database/schema.sql` referans (~765 satır)

**Değerlendirme:** ✅ Veritabanı şeması kapsamlı. ⚠️ Alembic migration dosyaları klasör yapısında görülmüyor; şema değişiklikleri `create_tables.py` script'i ile yönetiliyor.

---

## 6. API Endpoint Analiz

### 6.1. Mevcut API Grupları (18 router)

| Grup | Prefix | Endpoint Sayısı (tahmini) |
|------|--------|--------------------------|
| Health | `/health`, `/ready` | 2 |
| Auth | `/auth` | 3-4 (login, register, me) |
| Assets | `/assets` | 4-5 |
| Incidents | `/incidents` | 4-5 |
| Threats | `/threats` | 3-4 |
| Approvals | `/approvals` | 5-6 |
| LLM | `/llm` | 4-5 (chat, analyze/logs, analyze/threat, health) |
| Supervisor | `/supervisor` | 5-6 |
| Modules | `/modules` | 3-4 |
| Scans | `/scans` | 2-3 |
| Traffic | `/traffic` | 2-3 |
| Admin | — | 2-3 |
| Analytics | — | 2-3 |
| Notifications | — | 2-3 |
| API Keys | — | 3-4 |
| Models | — | 2-3 |
| Logs | `/logs` | 2-3 |
| WebSocket | — | 1-2 |

**Değerlendirme:** ✅ Kapsamlı API yapısı. ⚠️ Agent chat endpoint'i (`POST /api/v1/agent/chat`) henüz eklenmemiş.

---

## 7. Güvenlik Analiz

### 7.1. Kritik Bulgular 🔴

| # | Bulgu | Konum | Önem |
|---|-------|-------|------|
| 1 | **Hardcoded DB şifresi** (default) | `config.py:41` — `scout_secure_2024` | Orta |
| 2 | **Çift `secret_key` tanımı** — İkincisi (satır 75) birincisini (satır 44) eziyor; son değer `dev-secret-key-change-in-production` | `config.py:44,75` | Yüksek |
| 3 | **Windows debug log yolu** üretim kodunda — `c:\Users\erama\OneDrive\Desktop\Scout\.cursor\debug.log` dosyasına yazma denemeleri | `auth.py:111-124, 170+` | Yüksek |
| 4 | **`except Exception: pass`** — Sessiz hata yutma (debug log yazma bloklarında) | `auth.py:122,175,187,200` | Orta |
| 5 | **Bare `except:`** ifadesi | `endpoint_security/scanner.py:163` | Orta |
| 6 | **Docker Compose'da açık şifreler** — PgAdmin: `admin123`, Postgres: `scout_secure_2024` | `docker-compose.yml` | Düşük (geliştirme) |

### 7.2. Olumlu Güvenlik Özellikleri ✅

- **LLM Guard:** Prompt injection ve veri sızıntısı koruması (regex tabanlı, girdi/çıktı sanitizasyonu).
- **JWT Auth:** Bearer token ile API koruması; `require_superuser` decorator.
- **HITL (Human-in-the-Loop):** Kritik aksiyonlar onay gerektiriyor (PendingAction → ApprovalPolicy).
- **CORS:** Belirli originler ile sınırlı.
- **Model Router:** Fast/Reasoning/Default model ayrımı; hassas analizler yerel LLM üzerinden.

---

## 8. Test Analiz

| Kategori | Dosya | Test Sayısı (tahmini) |
|----------|-------|----------------------|
| Unit — Entities | `test_entities.py` | ~10 |
| Unit — Modules | `test_modules.py` | ~8 |
| Integration — API | `test_api.py` | ~3-5 |
| **Toplam** | **3 dosya** | **~20-23** |

**Test Kapsama Oranı:** Düşük. ~13.865 satır backend kodu için sadece ~443 satır test kodu.

### Eksik Test Alanları

- Ajan testleri (Orchestrator, Hunter, Stealth, Defense, Supervisor, Learning Engine)
- LLM Guard testleri
- API endpoint unit testleri (mock DB ile)
- Tool wrapper testleri (Nmap, tshark)
- Application service testleri (ActionExecutor, ApprovalService)
- Repository testleri

**Değerlendirme:** 🔴 Test kapsamı yetersiz. Kritik iş mantığı (ajan yönlendirme, güvenlik korumaları, onay akışı) test edilmiyor.

---

## 9. Tespit Edilen Sorunlar ve Öneriler

### 9.1. Yüksek Öncelikli 🔴

| # | Sorun | Öneri |
|---|-------|-------|
| 1 | `config.py`'de çift `secret_key` tanımı | İlk tanımı (satır 44) kaldırın; tek `secret_key` bırakın |
| 2 | `auth.py`'de Windows debug log kodu üretimde | `_is_db_connection_error()` içindeki `#region agent log` bloğunu tamamen kaldırın |
| 3 | Test kapsamı çok düşük (~3%) | Ajan, guard, service ve API katmanları için unit testler ekleyin; hedef: >60% kapsam |
| 4 | Alembic migration dosyaları eksik | `alembic init` yapıp şema değişikliklerini migration olarak yönetin |

### 9.2. Orta Öncelikli ⚠️

| # | Sorun | Öneri |
|---|-------|-------|
| 5 | Hunter/Stealth/Defense ajanları mock veri dönüyor | Tool Registry ile gerçek araç entegrasyonu (ROADMAP Faz 10) |
| 6 | Chat UI (LLM + Ajan) eksik | `/dashboard/chat` ve `/dashboard/agent-chat` sayfaları (TASKS'da aktif) |
| 7 | Bare `except:` ve `except Exception: pass` kullanımları | Spesifik exception'lar yakalansın; minimum loglama yapılsın |
| 8 | `scripts/` dizininde `__init__.py` eksik | Ekleyin (veya scripts'i package dışına çıkarın) |
| 9 | Frontend'de bazı sayfalar mock veri ile çalışıyor | Mock kaldırma (TASKS'da aktif) |
| 10 | Health endpoint'te DB/Redis kontrolü placeholder | Gerçek bağlantı kontrolü ekleyin |

### 9.3. Düşük Öncelikli 📝

| # | Sorun | Öneri |
|---|-------|-------|
| 11 | `database_url`'de default şifre var | Env variable'dan okunsun, default boş olsun |
| 12 | Docker Compose'da PgAdmin şifresi açık | Env variable'a taşıyın |
| 13 | TODOs — 7+ açık TODO/FIXME yorumu var | TASKS.md ile senkronize edin veya çözün |
| 14 | Frontend type tanımları (`@types/react: ^18`) React 19 ile uyumsuz olabilir | `@types/react` versiyonunu güncelleyin |

---

## 10. Tamamlanma Durumu Özeti

### Tamamlanan Fazlar ✅

| Faz | Açıklama | Durum |
|-----|----------|-------|
| Faz 5 | Mimari iskelet | ✅ Tamamlandı |
| Faz 6 | Error Handling & Entegrasyon | ✅ Tamamlandı |
| Faz 7 | Hafıza & Veritabanı | ✅ Tamamlandı |
| Faz 8.1 | Supervisor Agent | ✅ Tamamlandı |
| Faz 8.2 | Feedback Loop (Learning Engine) | ✅ Tamamlandı |

### Aktif / Planlanan Fazlar 🔄

| Faz | Açıklama | Durum |
|-----|----------|-------|
| Chat UI | LLM + Ajan sohbet arayüzü | 🔄 Başlamadı |
| Faz 8.3 | Anomaly Detection Engine | 📋 Planlandı |
| Faz 8.4 | Threat Intelligence Integration | 📋 Planlandı |
| Faz 9 | Multi-Model LLM Stratejisi | 📋 Planlandı |
| Faz 10 | Açık Kaynak Araç Entegrasyonu | 🔄 Altyapı hazır, entegrasyon bekliyor |
| Faz 11 | Advanced Dashboard & Visualization | 📋 Planlandı |

---

## 11. Genel Değerlendirme

### Güçlü Yönler 💪

1. **Sağlam mimari:** Clean Architecture / DDD prensipleri tutarlı uygulanmış
2. **Kapsamlı ajan sistemi:** LangGraph ile Orchestrator → Worker ajan döngüsü, Supervisor ve Learning Engine
3. **Plugin mimarisi:** Modül sistemi genişletilebilir (BaseModule → ModuleRegistry)
4. **Güvenlik katmanları:** LLM Guard, JWT auth, HITL onay, CORS
5. **Yerel LLM:** Ollama ile veri gizliliği ve sıfır API maliyeti
6. **Zengin frontend:** 19+ dashboard sayfası, 3D görselleştirme, gerçek zamanlı bileşenler
7. **İyi dokümantasyon:** `docs/` altında PROJECT_CONTEXT, TASKS, DONE, MODULES, ROADMAP

### İyileştirme Gereken Alanlar 📈

1. **Test kapsamı:** ~3% → hedef >60%
2. **Mock veri kaldırma:** Ajan ve frontend mock verileri gerçek entegrasyonlarla değiştirilmeli
3. **Debug kodu temizliği:** Üretim kodundaki Windows debug log yolları ve sessiz `except: pass` blokları kaldırılmalı
4. **Config temizliği:** Çift `secret_key`, default şifreler temizlenmeli
5. **Migration yönetimi:** Alembic ile şema versiyonlama

### Öncelik Sıralaması (Önerilen)

1. 🔴 Debug kodu ve config sorunlarını temizle (hızlı kazanım)
2. 🔴 Test kapsamını artır (kritik iş mantığı için)
3. ⚠️ Chat UI ekle (kullanıcı deneyimi)
4. ⚠️ Mock veri kaldır, gerçek araç entegrasyonu (Faz 10)
5. 📋 Anomaly Detection ve Threat Intelligence (Faz 8.3/8.4)

---

*Bu analiz raporu, projenin mevcut durumunu kapsamlı şekilde değerlendirmek amacıyla hazırlanmıştır. Tüm öneriler, mevcut ROADMAP ve TASKS dökümanları ile uyumludur.*
