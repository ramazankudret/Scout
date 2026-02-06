# Scout - Geliştirme Yol Haritası

## Tamamlanan Fazlar

### Faz 5: Mimari İskelet
- [x] Core modülleri, Guards, Agents, Dashboard sayfaları

### Faz 6: Error Handling & Entegrasyon
- [x] Backend Error Middleware & Logging
- [x] Agent Safe Execution
- [x] API Error Test Endpoint'leri
- [x] Frontend Logs Sayfası Bağlantısı

### Faz 7: Hafıza & Veritabanı (Memory)
- [x] PostgreSQL + pgvector kurulumu
- [x] Veritabanı Şeması (15 tablo, 463+ kolon)
- [x] SQLAlchemy ORM Modelleri
- [x] FastAPI Veritabanı Bağlantısı
- [x] Repository Katmanı (BaseRepository + özelleştirilmiş repository'ler)
- [x] API Endpoint'leri (Assets, Incidents CRUD)
- [x] Frontend API Client (Assets, Incidents, Health)
- [x] Frontend Assets & Incidents Sayfaları
- [x] Kullanıcı Auth (Login/Register)
- [x] Login & Register Sayfaları UI
- [x] Frontend Route Protection
- [x] Agent Monitor Canlı Takip Sayfası

### Faz 8 (Kısmi): Self-Healing & Adaptive Intelligence
- [x] Human-in-the-Loop Altyapısı (Backend: PendingAction, Frontend: Approvals UI)
- [x] Local LLM Entegrasyonu (Ollama - Llama 3.1, model router)
- [x] **Faz 8.1: Supervisor Agent** — SupervisorAgent sınıfı, health monitoring, otomatik restart (simülasyon), HITL eskalasyonu (Approvals UI’da görünür), Supervisor Dashboard UI (Restart, Son Olaylar, Learned Lessons), GET /supervisor/events
- [x] **Faz 8.2: Feedback Loop (Learning Engine)** — LearningEngine servisi, learned_lessons şema uyumu (agent_name, action_type, category, severity, prevention_strategy, recommended_checks, occurrence_count), başarısız aksiyon analizi (LLM), Supervisor→Learning Engine otomatik tetikleme, ActionExecutor’da get_prevention_checks / get_lesson_advice ön kontrol, Learned Lessons Supervisor sayfasında

---

## Aktif Faz: Sohbet, Araçlar, 8.3/8.4 ve Mock Kaldırma

### Kullanıcı–LLM Sohbet Arayüzü
- [ ] **Basit LLM sohbet** — `/dashboard/chat` (veya llm-chat): mevcut `POST /api/v1/llm/chat` ile mesaj listesi + input UI; Sidebar’da “Sohbet” linki.
- [ ] **Ajan sohbeti** — `/dashboard/agent-chat`: `POST /api/v1/agent/chat` ile agent_graph (Orchestrator → Hunter/Stealth/Defense) çalıştırma; kullanıcı tek sohbet kutusunda ajanlarla konuşur. İsteğe bağlı: SSE/WebSocket ile stream.

### Faz 8.3: Anomaly Detection Engine
- [ ] Feature extraction pipeline (asset/incident/execution metrikleri)
- [ ] Baseline fingerprinting (normal davranış)
- [ ] Unsupervised anomaly detection (PyOD / Isolation Forest)
- [ ] pgvector embedding similarity (opsiyonel)
- [ ] Real-time anomaly alerts
- [ ] Anomaly Score Timeline UI

### Faz 8.4: Threat Intelligence Integration
- [ ] External feed modülü (OTX, AbuseIPDB, VirusTotal)
- [ ] IoC (Indicators of Compromise) veritabanı
- [ ] Otomatik IoC eşleştirme
- [ ] Threat Intel Dashboard UI

### Faz 10: Açık Kaynak Araç Entegrasyonu (Tool Registry)

Tüm araçlar **ücretsiz ve açık kaynak**; lab / startup / öğrenci kurulumu için uygundur.

| Kategori        | Araç            | Kullanım amacı                          | Öncelik   |
|-----------------|-----------------|------------------------------------------|-----------|
| Keşif / Analiz  | **Nmap**        | Port/servis taraması (Hunter)            | 1 – Zorunlu |
| Keşif / Analiz  | **Wireshark (tshark)** | Paket analizi, pasif dinleme (Stealth) | 2 – Zorunlu |
| Keşif / Analiz  | **Masscan**     | Hızlı tarama (geniş ağ keşfi)            | 3         |
| Keşif / Analiz  | **Netdiscover** | Yerel ağ keşfi                           | 4         |
| Zafiyet         | **OpenVAS**     | Zafiyet taraması (Nmap sonrası CVE vb.)  | 5         |
| Savunma         | **Snort** / **Suricata** | IDS/IPS, log kaynağı, tespit kuralları | 6         |
| Pentest         | **Metasploit** (community) | Kontrollü pentest senaryoları        | Sonra     |
| Pentest         | THC Hydra, Aircrack-ng, John the Ripper | İleride (opsiyonel)              | Sonra     |

**Uygulama sırası önerisi:** Tool Registry (`backend/src/scout/tools/`) → Nmap → tshark → Hunter/Stealth modüllerinde stub kaldırma, ScanResult/DB’ye yazma → Masscan, OpenVAS, Netdiscover → Snort/Suricata log entegrasyonu → Metasploit (ayrı modül).

- [ ] Tool Registry (tools/ klasörü, get_tools, LangChain tool binding veya ajan içi çağrı)
- [ ] Nmap entegrasyonu (Hunter; ScanResult DB)
- [ ] Wireshark/tshark entegrasyonu (Stealth; paket gözlem/analiz)
- [ ] Masscan, Netdiscover, OpenVAS entegrasyonu
- [ ] Snort / Suricata log okuma ve incident/IoC besleme
- [ ] Firewall API (iptables/Windows Firewall) — Defense
- [ ] Mock veri kaldırma (frontend + backend); tüm veri gerçek DB/araçlardan

### Faz 11: Advanced Dashboard & Visualization
- [ ] Threat Heatmap (coğrafi)
- [ ] Agent Performance Grafiği
- [ ] Network Topology Visualization
- [ ] Vector Space Explorer (3D embedding viz) — mevcut VectorSpace gerçek veriyle
- [ ] Real-time WebSocket updates

---

## Faz 9: Multi-Model LLM Stratejisi

### Mevcut Modeller
- **Llama 3.1:8b** — Hızlı operasyonel görevler (routing, basit kararlar)
- **DeepSeek-R1:8b** — Derin reasoning, istihbarat analizi

### Planlanan Model Entegrasyonları
- [ ] **Llama Nemotron Nano (8B)** — RTX optimized, Ollama üzerinden
- [ ] **DeepSeek-R1:14B/32B** (Opsiyonel)

### Model Kullanım Stratejisi
| Task Type       | Model           | Reason        |
|-----------------|-----------------|---------------|
| Agent Routing   | Llama 3.1:8b    | Fast, simple  |
| Threat Analysis | DeepSeek-R1:8b  | Deep reason   |
| Attack Response | Nemotron Nano   | RTX optimized |
| Log Summarization | Llama 3.1:8b | Speed         |

---

## Öncelik Sıralaması

| Görev                  | Zorluk | Etki   | Durum    |
|------------------------|--------|--------|----------|
| Supervisor Agent       | 2      | 4      | Tamamlandı |
| Feedback Loop          | 3      | 5      | Tamamlandı |
| Chat UI (LLM + Ajan)   | 2      | 4      | Sırada   |
| Tool Registry + Nmap/tshark | 3 | 5      | Sırada   |
| Mock kaldırma          | 2      | 4      | Sırada   |
| Anomaly Detection (8.3)| 4      | 5      | Planlandı |
| Threat Intel (8.4)     | 2      | 4      | Planlandı |
| Açık kaynak araçlar (Masscan, OpenVAS, Snort vb.) | 3 | 4 | Planlandı |

---

*Son güncelleme: 2026-02-06*
