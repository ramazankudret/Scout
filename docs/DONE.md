# Scout - Yapılanlar

Bu dosya, projede ne zaman ne yapıldığının kısa kaydıdır. Tüm araçlar "daha önce ne ettik?" sorusunun cevabını buradan alır.

---

## 2026-02-06

- **Proje Analiz Raporu oluşturuldu.** `docs/PROJECT_ANALYSIS.md`: Mimari, kod metrikleri, güvenlik bulguları, test kapsamı, tamamlanma durumu, sorunlar ve öneriler. Kritik bulgular: çift `secret_key` tanımı (`config.py`), üretim kodunda Windows debug log yolu (`auth.py`), düşük test kapsamı (~3%), 7+ açık TODO.
- **Faz 8.1 ve 8.2 tamamlandı.** LearnedLesson şema uyumu; Supervisor → Learning Engine otomatik tetikleme; HITL eskalasyonu (supervisor_escalation, Approvals UI); GET /supervisor/events; Supervisor Dashboard (Restart, Son Olaylar, tema); ActionExecutor get_prevention_checks/get_lesson_advice; PendingActionRepository create/update entity; get_summary by_severity.
- **ROADMAP ve docs güncellendi.** Faz 8.1/8.2 tamamlandı; Chat UI, Faz 8.3/8.4, Faz 10 açık kaynak araç listesi (Nmap, Wireshark/tshark, Masscan, Netdiscover, OpenVAS, Snort/Suricata, Metasploit sonra); MODULES.md, PROJECT_CONTEXT.md, TASKS.md uyumlu hale getirildi.
- **Dashboard ve arayüz revizyonu.** API client: threatsApi (list, getStatsSummary), supervisorApi (getStatus, getSummary, getLearningSummary), modulesApi (list); Authorization header (Bearer token) eklendi. Dashboard: gerçek KPI kartları (tehdit, varlık, onay, olay), Recent Activity incidentsApi.getRecent ile; PipelineViz bileşeni (Orchestrator → Hunter/Stealth/Defense, supervisor status); VectorSpace assetsApi ile besleniyor (asset’ten node, subnet/zone, risk_score ile anomaly). Sidebar: Command Center, Operations, Intelligence, System grupları ve alt menü. Pipeline sayfası (/dashboard/pipeline). QueryProvider dashboard layout’ta.
- **Docs yapısı eklendi.** `docs/PROJECT_CONTEXT.md`, `TASKS.md`, `DONE.md`, `MODULES.md`, `AI_CONTEXT.md` oluşturuldu. Birden fazla AI aracı (Cursor, Claude, Copilot, GPT, Antigravity IDE) ile tutarlı bağlam için tek kaynak olsun diye.
- **Lesson Model altyapısı.** Config (ollama_lesson_model, lesson_export_dir, lesson_min_samples_for_training, lesson_model_base, lesson_model_output_dir), export servisi (application/services/lesson_export_service.py), export_lessons.py ve train_lesson_model.py script'leri, Learning Engine'de get_lesson_advice (lesson model vs RAG), .env.example ve .gitignore güncellemesi, docs (TASKS, MODULES, DONE) güncellendi.
- **Log analizi verimlilik + hibrit mod.** Config (log_max_lines, log_hybrid_max_lines, log_high_load_threshold_lines, log_priority_keywords, log_priority_severity_patterns), log_preprocessor (application/services/log_preprocessor.py), API /analyze/logs ön işlem + yoğunlukta fast model + analysis_meta, OllamaService.analyze_logs tam content kullanımı.

---

## Daha Önce (Özet)

- **Mimari iskelet:** Core, Guards, Agents, Dashboard sayfaları.
- **Error handling:** Backend middleware, agent safe execution, frontend logs.
- **Veritabanı:** PostgreSQL + pgvector, SQLAlchemy ORM, repository katmanı, Assets/Incidents CRUD, auth (login/register), route protection, agent monitor sayfası.
- **Human-in-the-Loop:** Backend ActionRequest, frontend Approvals UI.
- **Ollama entegrasyonu:** Llama 3.1, model router (fast/reasoning/default).
- **Supervisor Agent:** Health monitoring, heartbeat, restart, HITL eskalasyonu (Approvals UI), SupervisorRepository, Supervisor Dashboard UI, events API.
- **Learning Engine:** Başarısızlık analizi, LLM ile ders çıkarma, DB + cache, LearnedLesson şema uyumu, Supervisor tetikleme, ActionExecutor ön kontrol.

Detaylı faz listesi için `docs/ROADMAP.md` kullanılır.

---

*Yeni iş yapıldıkça buraya tarih + kısa madde ekleyin.*
