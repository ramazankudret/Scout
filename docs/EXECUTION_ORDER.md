# Nereden Başlayalım — Adım Adım Çalışma Sırası

Agent modunda sırayla uygula. Her adım bitince bir sonrakine geç.

---

## Adım 1: Backend — Hunter’a `command` ve `steps` ekle (ilk oturum)

**Amaç:** API’den dönen yanıtta gerçek çalıştırılan komut ve (varsa) çıktı olsun; frontend bunu gösterebilsin.

**Yapılacaklar:**
- `backend/src/scout/modules/hunter/module.py` içinde:
  - `scan_host`: Nmap’ten dönen `result.data` içinden `command` al; dönüş dict’ine `command` ekle. Port/servis bilgisinden kısa bir `process_output` metni üret (örn. "PORT STATE SERVICE\n8000/tcp open http-alt") ve `steps: [{ "command": "...", "output": "...", "status": "success" }]` formatında ekle.
  - CIDR keşif (`_discover_subnet`): Nmap veya Netdiscover çağrısından komut/çıktıyı topla; tek sonuç dict’ine `command` ve `steps` ekle.
- Hunter’ın `execute` içinde döndürdüğü `findings` / `data` bu yeni alanları içersin. Modules API zaten `data`’yı olduğu gibi döndürüyor.

**Kontrol:** `POST /api/v1/modules/hunter/execute` ile tarama yap; response `data` içinde `command` ve `steps` (veya `process_output`) görünmeli.

---

## Adım 2: Frontend — ProcessOutputBlock bileşeni (ikinci oturum)

**Amaç:** Gerçek çalışan process’leri terminal benzeri kod kutusunda göster.

**Yapılacaklar:**
- Yeni dosya: `frontend/src/components/dashboard/ProcessOutputBlock.tsx`
  - Props: `steps?: Array<{ command: string; output?: string; status?: string }>` veya tek `command` + `output`.
  - Görünüm: Monospace font, koyu arka plan, ince border; komut satırı öncesi `$`; çıktı aşağıda. Birden fazla step varsa hepsini liste halinde göster (Step 1, Step 2…).
- Bileşeni export et; henüz hiçbir sayfaya bağlama (Adım 3’te Hunter’a bağlanacak).

**Kontrol:** Storybook yoksa, geçici olarak Hunter sayfasına `<ProcessOutputBlock steps={[{ command: "nmap -sT 127.0.0.1", output: "8000/tcp open", status: "success" }]} />` koyup ekranda göründüğünü doğula; sonra bu geçici kodu kaldırıp Adım 3’te gerçek veriyle bağla.

---

## Adım 3: Frontend — Hunter sayfasında process kutucuklarını kullan (üçüncü oturum)

**Amaç:** Tarama sonucu döndüğünde aynı sayfada "Execution / Process" alanında gerçek komut ve çıktı görünsün.

**Yapılacaklar:**
- `frontend/src/app/dashboard/hunter/page.tsx`:
  - `modulesApi.execute("hunter", ...)` yanıtından `result.data` içindeki `steps`, `command`, `process_output` al.
  - Sonuç bölümünde (open ports / services’in yanında veya üstünde) `<ProcessOutputBlock steps={...} />` veya `command` + `process_output` ile render et. Veri yoksa bileşeni gösterme veya "Komut çıktısı yok" mesajı ver.
- Tarama bitince hem port/servis listesi hem de process kutucukları aynı anda görünmeli.

**Kontrol:** Hunter’da bir IP tara; sayfada "Execution" / process kod kutusunda gerçek nmap komutu ve çıktı görünmeli.

---

## Adım 4: Frontend — Global tema ve SOC hissi (dördüncü oturum)

**Amaç:** Tüm dashboard’da koyu, ince çizgili, SOC/panel hissi.

**Yapılacaklar:**
- `frontend/src/app/globals.css`: Panel/card için daha koyu renkler, 8px grid (varsa), ince border, terminal/monospace alanları için CSS değişkeni.
- `frontend/tailwind.config.ts`: Scout paletinde `scout.panel-border`, `scout.terminal` (ve gerekirse `scout.grid`) ekle veya güncelle.
- `frontend/src/app/dashboard/layout.tsx`: Ana içerik alanını CSS Grid ile 2–3 sütunlu yapıya getir (büyük ekran).
- `frontend/src/components/layout/Sidebar.tsx`: Daha kompakt, ince border, panel arka planı; metin/ikon dengesi.

**Kontrol:** Dashboard ve Hunter sayfası açıldığında genel görünüm daha koyu ve "operasyon merkezi" hissi veriyor mu bak.

---

## Adım 5: Frontend — VectorSpace görsel seviyesini yükselt (beşinci oturum)

**Amaç:** 3D topoloji widget’ı daha elit / gelişmiş görünsün.

**Yapılacaklar:**
- `frontend/src/components/dashboard/VectorSpace.tsx`:
  - Arka plan: Daha zengin yıldız, fog/atmosphere; gradient derinleştir.
  - CoreSphere: Daha "tech" (wireframe + iç ışık, orbit halkası); emissive + Bloom vurgula.
  - Düğümler: Material iyileştir; tehdit/hover’da outline veya glow.
  - Bağlantı çizgileri: İnce tüp veya dashed animasyon; tehdit vektöründe kısa pulse.
  - DataStreams: Nokta/küre, renk çeşidi; gerekirse çizgi boyunca akan partikül.
  - Post-processing: Bloom ayarı; isteğe bağlı hafif Vignette.

**Kontrol:** Dashboard ana sayfada VectorSpace açıldığında görsel olarak daha "premium" hissettirmeli.

---

## Adım 6 ve sonrası (isteğe bağlı)

- **Ortak panel bileşeni:** Koyu arka plan, başlık çubuğu, status led; Hunter ve diğer sayfalarda Card yerine kullan.
- **Diğer sayfalar:** Assets, Incidents, Scans vb. aynı panel/grid stilinde.
- **Chat UI, Loading/Toast, stub kaldırma:** `docs/FRONTEND_IMPROVEMENTS.md` dosyasındaki sıraya göre ilerle.

---

## Özet sıra

| Sıra | Adım | Ne zaman biter |
|------|------|----------------|
| 1 | Backend: Hunter’a command/steps | API yanıtında `command` ve `steps` var |
| 2 | ProcessOutputBlock bileşeni | Bileşen render ediyor (test verisiyle) |
| 3 | Hunter sayfasına process kutusu | Tarama sonrası gerçek komut/çıktı görünüyor |
| 4 | Global tema + SOC layout | Dashboard genelinde koyu/panel hissi |
| 5 | VectorSpace görsel upgrade | 3D widget daha elit görünüyor |

**Agent moduna geçince:** "Adım 1’i uygula: Backend Hunter’a command ve steps ekle" de; bitince "Adım 2’ye geç" deyip devam et.
