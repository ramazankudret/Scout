# Scout - Proje Bağlamı

Bu dosya, projeye (Cursor, Claude, Copilot, GPT vb.) dahil olan her araç ve kişi için tek kaynak gerçektir. Scout hakkında karar verirken veya kod yazarken önce bu belgeye bakın.

---

## Proje Nedir?

**Scout**, otonom bir siber güvenlik ajanıdır. Hem **Red Team** (saldırı simülasyonu, zafiyet tarama) hem **Blue Team** (savunma, izleme, tehdit analizi) işleri yapar. Ayrıca **kendi LLM’lerinin ve başkalarının kullandığı LLM sistemlerinin güvenliğini** sağlamak ana hedeflerden biridir.

- **Yerel LLM:** Ollama ile (Llama, Nemotron, DeepSeek-R1) çalışır; veri dışarı çıkmaz, API maliyeti yok.
- **Ürün hedefi:** Ürünleştirilip şirket kurulması hedefleniyor (Türkiye ve potansiyel global pazar).

---

## Teknik Mimari (Kısa)

- **Backend:** Python 3.11+, FastAPI (async), Clean Architecture / DDD.
- **Veritabanı:** PostgreSQL + pgvector (semantik arama için).
- **ORM:** SQLAlchemy (async) + Alembic.
- **LLM:** LangChain + Ollama (yerel modeller). Model Router: FAST (routing) / REASONING (analiz) / DEFAULT.
- **Ajanlar:** LangGraph ile Orchestrator → Hunter, Stealth, Defense döngüsü. Supervisor ve Learning Engine grafik dışında çalışır.
- **Frontend:** Next.js 14+ (App Router), Tailwind, Shadcn UI.

**Klasör yapısı (backend):**

- `domain/` — Entity, value object, interface (port). İş mantığı; altyapıya bağımlılık yok.
- `application/` — Use case, servis, DTO.
- `infrastructure/` — API, DB, repository implementasyonları, Ollama, WebSocket.
- `agents/` — BaseAgent, Orchestrator, Hunter, Stealth, Defense, Supervisor, Learning Engine.
- `modules/` — Hunter, Stealth, Defense modülleri (plugin benzeri); ModuleRegistry.
- `core/` — Config, logging, exceptions, model_router, state, graph.

---

## Kurallar ve Standartlar

- **Clean Architecture:** Domain’e infrastructure sızmasın. Repository’ler domain interface’lerini implement etsin.
- **Tip güvenliği:** Python’da mypy uyumlu type hint; TypeScript’te interface.
- **Async:** Tüm I/O async/await.
- **Hata:** Özel `ScoutError`; `except Exception:` kullanılmaz.
- **Loglama:** Kritik işlemlerde yapısal log.
- **Veri erişimi:** Domain’deki `ISupervisorRepository`, `ILearningRepository` vb. kullanılsın; doğrudan DB/ORM domain’e taşınmasın.

---

## Ajanlar (Özet)

| Ajan | Rol |
|------|-----|
| **Orchestrator** | Kullanıcı isteğini yorumlar; Hunter / Stealth / Defense / (ileride Intelligence) yönlendirir. |
| **Hunter** | Proaktif tarama (port, zafiyet). Tool Registry ile Nmap, Masscan, OpenVAS entegrasyonu planlanıyor; şu an stub. |
| **Stealth** | Pasif izleme, log/trafik analizi. Wireshark/tshark entegrasyonu planlanıyor; şu an stub. |
| **Defense** | Savunma aksiyonları (firewall, engelleme). HITL ve action_executor ile bağlı; Snort/Suricata log beslemesi planlanıyor. |
| **Supervisor** | Ajan sağlığı, heartbeat, otomatik restart, HITL eskalasyonu. |
| **Learning Engine** | Başarısız aksiyonları analiz eder, ders çıkarır, DB’ye yazar. |
| **Intelligence Agent** | Planlanan. Cihaz/IP/ağ verisinden istihbarat çıkarımı; knowledge graph + hibrit (kural + LLM). |

---

## Planlanan Büyük Özellikler

- **Kullanıcı–LLM Sohbet Arayüzü:** Basit LLM sohbet sayfası (`/dashboard/chat`) ve ajan sohbeti (`/dashboard/agent-chat`) — kullanıcı Orchestrator/Hunter/Stealth/Defense ile tek arayüzden konuşur.
- **Tool Registry (Açık Kaynak Araçlar):** Keşif/Analiz: Nmap, Wireshark (tshark), Masscan, Netdiscover. Zafiyet: OpenVAS. Savunma: Snort, Suricata (log/IDS). İleride Pentest: Metasploit (community). Tümü ücretsiz ve açık kaynak; Hunter/Stealth/Defense modülleriyle entegre edilecek.
- **Intelligence Agent:** Yeni ajan; istihbarat çıkarımı, knowledge graph, hibrit yaklaşım.
- **Threat Intelligence:** OTX, AbuseIPDB, VirusTotal; IoC veritabanı ve otomatik eşleştirme.
- **Anomaly Detection:** Feature extraction, baseline, PyOD/Isolation Forest, anomali skoru, uyarılar, timeline UI.
- **Mock Kaldırma:** Tüm stub/mock veri kaldırılacak; frontend ve backend gerçek DB ve gerçek araçlara bağlanacak.
- **Docs:** Tüm araçların aynı bağlamda çalışması için `docs/` (PROJECT_CONTEXT, TASKS, DONE, MODULES, ROADMAP).

Detaylı faz listesi için `docs/ROADMAP.md` kullanılır.

---

## Güncelleme

Bu dosyayı mimari veya proje hedefleri değiştiğinde güncelleyin. Tarih ekleyebilirsiniz.

*Son güncelleme: 2026-02-06 (ROADMAP ve araç listesi güncellendi).*
