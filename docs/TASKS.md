# Scout - Güncel Görevler

Bu dosya, şu an yapılması gereken veya sıradaki işleri listeler. Herhangi bir AI aracı veya geliştirici buradan "şu an ne yapıyoruz?" sorusunun cevabını alır.

**Kullanım:** Yeni görev ekle, tamamlananı işaretle. ROADMAP büyük fazlar için, TASKS günlük/sprint seviyesi için.

---

## Aktif / Öncelikli

- [ ] **Chat UI (LLM + Ajan)** — Basit LLM sohbet sayfası (`/dashboard/chat`, mevcut `/llm/chat` API) ve ajan sohbeti (`/dashboard/agent-chat`, `POST /api/v1/agent/chat` ile agent_graph). Sidebar’da Sohbet linki.
- [ ] **Tool Registry + açık kaynak araçlar** — `backend/src/scout/tools/`: Nmap, Wireshark/tshark, Masscan, Netdiscover, OpenVAS, Snort/Suricata (log). Hunter/Stealth modüllerinde stub kaldırma, gerçek araç çağrısı ve ScanResult/DB yazma. Detay: `docs/ROADMAP.md` Faz 10.
- [ ] **Mock kaldırma** — Frontend: ai-security ve VectorSpace gerçek API ile; backend: modül stub’ları tool çıktısı ve DB ile değiştirilecek.

---

## Sırada (Kısa Vadeli)

- [x] **ROADMAP güncellemesi** — Faz 8.1/8.2 tamamlandı; Chat UI, 8.3, 8.4, Faz 10 araç listesi eklendi. (Tamamlandı.)
- [x] **LearnedLesson ↔ Learning Engine uyumu** — Şema ve create_tables migrasyonu yapıldı. (Tamamlandı.)
- [ ] **Faz 8.3: Anomaly Detection** — Feature extraction, baseline, PyOD/Isolation Forest, anomaly alerts, timeline UI.
- [ ] **Faz 8.4: Threat Intelligence** — OTX, AbuseIPDB, VirusTotal; IoC DB, eşleştirme, Threat Intel Dashboard.
- [ ] **Learning Engine embedding** — Ders kaydederken vector_embedding; find_similar anlamlı kullanım.

---

## Orta / Uzun Vadeli (ROADMAP ile uyumlu)

- [ ] Lesson Model LoRA eğitim adımı (gerçek) — train_lesson_model.py içinde HF PEFT veya Unsloth.
- [ ] Intelligence Agent tasarımı — Cihaz/IP/ağ verisinden istihbarat; graph’a node, Orchestrator yönlendirme.
- [ ] Metasploit (community) entegrasyonu — Kontrollü pentest senaryoları (Faz 10 sonrası).
- [ ] Supervisor gerçek restart mantığı (process/container).
- [ ] Docs tutarlılığı — Yeni özellik veya mimari değişiklikte PROJECT_CONTEXT, MODULES, ROADMAP güncelle.

---

*Son güncelleme: 2026-02-06*
