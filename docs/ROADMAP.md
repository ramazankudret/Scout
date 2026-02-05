# Scout - Geliştirme Yol Haritası

## ✅ Tamamlanan Fazlar

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
- [x] Repository Katmanı (BaseRepository + 5 özelleştirilmiş)
- [x] API Endpoint'leri (Assets, Incidents CRUD)
- [x] Frontend API Client (Assets, Incidents, Health)
- [x] Frontend Assets & Incidents Sayfaları
- [x] Kullanıcı Auth (Login/Register)
- [x] Login & Register Sayfaları UI
- [x] Frontend Route Protection
- [x] Agent Monitor Canlı Takip Sayfası

### Faz 8: Self-Healing & Adaptive Intelligence (Kısmi)
- [x] Human-in-the-Loop Altyapısı (Backend: ActionRequest, Frontend: Approvals UI)
- [x] Local LLM Entegrasyonu (Ollama - Llama 3.1)

---

## 🔄 Aktif Faz: Faz 8 Devamı + Mimari Güçlendirme

### Faz 8.1: Supervisor Agent (Self-Healing)
- [ ] `SupervisorAgent` sınıfı oluştur
- [ ] Agent health monitoring sistemi
- [ ] Otomatik restart mekanizması
- [ ] HITL eskalasyon entegrasyonu
- [ ] Supervisor Dashboard UI

### Faz 8.2: Feedback Loop (Learning Engine)
- [ ] `LearningEngine` servisi
- [ ] `learned_lessons` veritabanı tablosu
- [ ] Başarısız aksiyon analizi (LLM ile)
- [ ] Strateji güncelleme mekanizması
- [ ] Learned Lessons Dashboard UI

### Faz 8.3: Anomaly Detection Engine
- [ ] Feature extraction pipeline
- [ ] Baseline fingerprinting (normal davranış)
- [ ] Unsupervised anomaly detection (PyOD/Isolation Forest)
- [ ] pgvector embedding similarity
- [ ] Real-time anomaly alerts
- [ ] Anomaly Score Timeline UI

### Faz 8.4: Threat Intelligence Integration
- [ ] External feed modülü (OTX, AbuseIPDB, VirusTotal)
- [ ] IoC (Indicators of Compromise) veritabanı
- [ ] Otomatik IoC eşleştirme
- [ ] Threat Intel Dashboard UI

---

## 🧠 Faz 9: Multi-Model LLM Stratejisi

### Mevcut Modeller
- **Llama 3.1:8b** - Hızlı operasyonel görevler (routing, basit kararlar)
- **DeepSeek-R1:8b** - Derin reasoning, istihbarat analizi

### Planlanan Model Entegrasyonları
- [ ] **Llama Nemotron Nano (8B)** - RTX optimized, agentic AI
  - NVIDIA RTX 4060 için optimize
  - FP8 inference desteği
  - Ollama üzerinden entegrasyon
  
- [ ] **DeepSeek-R1:14B/32B** (Opsiyonel)
  - Daha güçlü reasoning için
  - 14B: 16GB VRAM gerektirir
  - 32B: Offloading ile çalışabilir

### Model Kullanım Stratejisi
```
┌─────────────────────────────────────────────────────────────┐
│                    Scout Model Router                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Task Type          │  Model                  │ Reason       │
│  ─────────────────────────────────────────────────────────  │
│  Agent Routing      │  Llama 3.1:8b          │ Fast, simple │
│  Threat Analysis    │  DeepSeek-R1:8b        │ Deep reason  │
│  Attack Response    │  Nemotron Nano:8b      │ RTX optimized│
│  Code Generation    │  DeepSeek-R1:8b        │ Accuracy     │
│  Log Summarization  │  Llama 3.1:8b          │ Speed        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Faz 10: Tool Entegrasyonu & Real-World Testing

- [ ] Nmap Scanner entegrasyonu
- [ ] Firewall API (iptables/Windows Firewall)
- [ ] DVWA Test Ortamı kurulumu
- [ ] Penetration Testing senaryoları

---

## 📊 Faz 11: Advanced Dashboard & Visualization

- [ ] Threat Heatmap (coğrafi)
- [ ] Agent Performance Grafiği
- [ ] Network Topology Visualization
- [ ] Vector Space Explorer (3D embedding viz)
- [ ] Real-time WebSocket updates

---

## 📅 Öncelik Sıralaması

| Görev | Zorluk | Etki | Status |
|-------|--------|------|--------|
| Supervisor Agent | ⭐⭐ | ⭐⭐⭐⭐ | 🔜 Next |
| Feedback Loop | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🔜 Next |
| Nemotron Entegrasyonu | ⭐⭐ | ⭐⭐⭐⭐ | 🔜 Next |
| Anomaly Detection | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Planned |
| Threat Intel Feed | ⭐⭐ | ⭐⭐⭐ | Planned |
| Tool Integration | ⭐⭐⭐ | ⭐⭐⭐⭐ | Planned |

---

*Son Güncelleme: 2026-02-05*
