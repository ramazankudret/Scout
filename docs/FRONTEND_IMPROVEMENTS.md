# Frontend için Geliştirme Önerileri

Bu dosya, Scout dashboard ve genel frontend için mevcut SOC/Process/VectorSpace planına **ek** yapılabilecek geliştirmeleri listeler. Öncelik ve kapsam ihtiyaca göre seçilebilir.

---

## 1. Yeni sayfalar ve özellikler (ROADMAP uyumlu)

| Özellik | Açıklama |
|--------|----------|
| **Chat UI (LLM sohbet)** | `/dashboard/chat` — `POST /api/v1/llm/chat` ile mesaj listesi + input; Sidebar'da "Sohbet" linki. Markdown render, mesaj geçmişi, model seçimi (opsiyonel). |
| **Ajan sohbeti** | `/dashboard/agent-chat` — Orchestrator/Hunter/Stealth/Defense ile tek arayüzden konuşma; `POST /api/v1/agent/chat`. İsteğe bağlı: SSE/WebSocket stream, "typing" göstergesi. |
| **Anomaly Score Timeline** (Faz 8.3) | Anomali skorunun zaman içinde değişimini gösteren grafik (Recharts); eşik çizgisi, olay işaretleri. |
| **Threat Intel Dashboard** (Faz 8.4) | IoC listesi, OTX/AbuseIPDB/VirusTotal sonuçları için kartlar veya tablo; "match" vurgulama. |
| **Real-time güncellemeler** | WebSocket (mevcut `/ws`) ile approvals, notifications, topology; canlı badge/sayaç veya liste güncellemesi. Polling fallback. |

---

## 2. UX ve kalite

- **Loading / skeleton:** Tüm liste ve detay sayfalarında tutarlı skeleton veya spinner (React Query `isPending`); Assets, Incidents, Scans, Approvals, Traffic.
- **Error boundary:** Route veya layout seviyesinde Error Boundary; "Yeniden dene" ve log/feedback.
- **Empty state:** Veri yokken anlamlı mesaj + aksiyon (örn. "Henüz asset yok — Hunter ile tara", "Onay bekleyen aksiyon yok").
- **Toast / bildirim:** Başarılı işlem veya hata için toast (sonner veya Shadcn toast); API hatalarında kullanıcıya net mesaj.
- **Form validasyonu:** Login/Register ve formlu sayfalarda Zod + react-hook-form ile tutarlı validasyon ve alan hata mesajları.

---

## 3. Eksik ve stub içeriklerin doldurulması

- **Defense:** "Blocked Entities — 12 Active" şu an mock; gerçek engellenen IP/range listesi API'den gelmeli. Global Threat Map placeholder yerine basit harita veya "Coming soon".
- **Stealth:** "Export PCAP" butonu işlevsel hale getirilmeli veya stub ise devre dışı/Coming soon.
- **Charts, AI-Security, Security:** Mock veri varsa gerçek API'ye geçiş veya "Demo verisi" etiketi.

---

## 4. Teknik ve erişilebilirlik

- **i18n:** Kullanıcı locale (docs'ta `locale: tr`); kritik etiketler için TR/EN seçimi (next-intl veya benzeri). Önce Türkçe sabit, sonra EN.
- **Erişilebilirlik (a11y):** Odak yönetimi (modal, sidebar), aria-label/aria-live, kontrast. Özellikle formlar ve tehlikeli aksiyonlar (Block IP, Isolate).
- **Responsive:** Sidebar mobilde drawer/collapse; tabloların yatay kaydırma veya kart görünümü; Hunter/Stealth formlarında küçük ekranda tek sütun.
- **Tema:** next-themes ile light/dark geçişi tutarlı kullanım (tüm sayfalarda theme değişkenleri).

---

## 5. Bileşen ve tasarım sistemi

- **Ortak panel bileşeni:** SOC planındaki "panel" (başlık çubuğu, border, status led) tüm dashboard sayfalarında; Card yerine veya Card varyantı.
- **DataTable:** Assets, Incidents, Scans, Traffic için ortak tablo (sıralama, filtre, sayfalama); Shadcn Table veya custom.
- **Filtre ve arama:** Liste sayfalarında tutarlı filtre çubuğu (tarih aralığı, durum, tip); URL query ile state senkronu.
- **Klavye kısayolları (opsiyonel):** "G then H" → Hunter, "G then A" → Assets; "?" ile kısayol paneli.

---

## 6. Özet öncelik matrisi

| Öncelik | Ne | Neden |
|--------|-----|-------|
| **Yüksek** | Chat UI (LLM) | ROADMAP'te sırada, kullanıcı değeri yüksek |
| **Yüksek** | Loading / Empty / Toast | Tüm sayfalarda UX tutarlılığı |
| **Orta** | Ajan sohbeti, WebSocket canlı güncelleme | Ürün farkı, "canlı" his |
| **Orta** | Defense/Stealth stub kaldırma | Sayfa güvenilirliği |
| **Orta** | DataTable + filtre | Liste sayfalarında verimlilik |
| **Düşük** | i18n, a11y, kısayollar | Uzun vadeli kalite ve erişilebilirlik |

---

*Mevcut plandaki SOC overhaul, Process kod kutucukları ve VectorSpace gelişmiş görselleri ile birlikte bu maddeler frontend yol haritasını oluşturur.*
