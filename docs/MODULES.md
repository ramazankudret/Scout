# Scout - Modüller ve Klasörler (Ne Ne İşe Yarıyor)

Bu dosya, proje içinde hangi klasör ve modülün ne işe yaradığını kısaca açıklar. Yeni bir araca veya geliştiriciye "bu dosya/klasör neden var?" sorusunun cevabı buradan verilir.

---

## Backend (`backend/src/scout/`)

### `core/`
- **config.py** — Ortam değişkenleri, Pydantic Settings (Ollama URL, model isimleri, DB URL, lesson model, lesson_export_dir vb.).
- **logger.py / logging.py** — Yapısal loglama.
- **exceptions.py / error_handler.py** — ScoutError, safe_execute decorator.
- **state.py** — LangGraph için AgentState (messages, current_agent, findings vb.).
- **graph.py** — LangGraph workflow: Orchestrator → Hunter/Stealth/Defense, router, kenarlar.
- **model_router.py** — LLM seçimi: FAST (routing), REASONING (analiz), DEFAULT.
- **security.py, licensing.py** — Güvenlik ve lisans yardımcıları.

### `domain/`
- **entities/** — Threat, Asset, PendingAction, ApprovalPolicy vb.
- **events/** — Domain event (approval events vb.).
- **interfaces/repositories.py** — Portlar: Repository, IThreatRepository, ISupervisorRepository, ILearningRepository vb.
- **value_objects/** — Value object’ler (varsa).

Domain katmanı altyapıya bağımlı olmamalı; sadece interface’lere referans verir.

### `application/`
- **services/** — Action executor, approval service, timeout service, lesson_export_service, log_preprocessor, anomaly_service (planlanan) vb.
- **dto/** — Data transfer object’ler.

### `agents/`
- **base.py** — BaseAgent; tüm ajanlar buradan türer.
- **implementations.py** — OrchestratorAgent, HunterAgent, StealthAgent, DefenseAgent. Orchestrator LLM ile yönlendirme yapar; Hunter/Stealth/Defense modül çağrısı ve gerçek araç entegrasyonu planlanıyor (Tool Registry).
- **supervisor.py** — SupervisorAgent: ajan sağlığı, heartbeat, restart, HITL eskalasyonu (Approvals UI), LLM ile failure analizi, Learning Engine tetikleme. Global `supervisor` instance.
- **learning_engine.py** — LearningEngine: başarısız aksiyon analizi (LLM), ders çıkarma, DB + cache, get_lesson_advice (lesson model / RAG). Global `learning_engine` instance.

### `modules/`
- **base.py** — BaseModule, ExecutionContext, ModuleMode, ModuleResult.
- **registry.py** — ModuleRegistry (singleton): modül kayıt, execute, execute_all.
- **hunter/** — Proaktif tarama; gerçek araç entegrasyonu Faz 10 ile gelecek (Nmap, Masscan, OpenVAS vb.).
- **stealth/** — Pasif izleme; gerçek araç entegrasyonu Faz 10 ile gelecek (Wireshark/tshark).
- **defense/** — Savunma aksiyonları (block_ip vb.), HITL ve action_executor ile bağlı.

### `tools/` (Planlanan)
- **Tool Registry** — Açık kaynak araçların LLM/ajanlara sunulması: Nmap, Wireshark (tshark), Masscan, Netdiscover, OpenVAS, Snort/Suricata log okuma, ileride Metasploit. Her araç için wrapper (nmap_tool, tshark_tool vb.) ve LangChain tool binding veya ajan içi çağrı.

### `infrastructure/`
- **api/v1/** — FastAPI route’lar: health, auth, assets, incidents, threats, approvals, supervisor, llm, logs, models, websocket, analytics, admin, notifications, api_keys vb. Planlanan: agent/chat (ajan sohbeti).
- **database/** — SQLAlchemy modelleri (User, Asset, Incident, LearnedLesson, SupervisorState, ScanResult vb.), session, pgvector.
- **repositories/** — Tüm repository implementasyonları.
- **llm/** — Ollama servisi (LangChain ChatOllama).
- **websocket/** — WebSocket manager (bildirimler, HITL).
- **tasks/** — Arka plan işleri (timeout processor vb.).
- **threat_intel/** (Planlanan) — OTX, AbuseIPDB, VirusTotal client’ları; IoC veritabanı ve eşleştirme.

### `guards/`
- **llm_guard.py** — Girdi sanitization, prompt injection / tehdit tespiti.

### `main.py`
- FastAPI uygulaması, router’lar, lifespan (supervisor.start, learning_engine.start).

### `scripts/`
- **create_tables.py** — Tablo oluşturma ve learned_lessons migrasyonu.
- **export_lessons.py** — learned_lessons → JSONL.
- **train_lesson_model.py** — Eğitim iskeleti (LoRA ileride).

---

## Frontend (`frontend/`)

- **src/app/** — Next.js App Router: dashboard, agents, approvals, assets, incidents, hunter, stealth, defense, supervisor, settings, login, register, charts, users, logs, notifications, pipeline, ai-security. Planlanan: chat (LLM sohbet), agent-chat (ajan sohbeti).
- **src/components/** — UI bileşenleri, layout (Sidebar), auth (ProtectedRoute), dashboard (VectorSpace, PipelineViz vb.).
- **Tailwind + Shadcn** — Scout tema (scout-panel, scout-border, scout-primary vb.).

---

## Diğer

- **docker-compose.yml, docker/** — Servislerin container ile çalıştırılması.
- **database/schema.sql** — Ham SQL şema (referans); asıl ORM `infrastructure/database/`.

---

*Yeni modül veya klasör eklendiğinde buraya kısa açıklama ekleyin.*

*Son güncelleme: 2026-02-06*
