# AI Araçları İçin Kısa Talimat

Bu proje (Scout) birden fazla AI aracı ile geliştiriliyor: Cursor, GPT+Codex, Claude Pro Code, GitHub Copilot, Antigravity IDE. Tutarlılık için lütfen şu adımları izleyin.

---

## Projeye başlarken

1. **Önce `docs/PROJECT_CONTEXT.md` okuyun.** Proje nedir, mimari nasıl, kurallar neler — tek kaynak orası.
2. **`docs/TASKS.md`** — Şu an ne yapılıyor, sıradaki işler neler, oradan bakın.
3. **`docs/DONE.md`** — Son zamanlarda ne yapıldı; değişiklik önerirken çakışma yaratmamak için göz atın.
4. **Modül/klasör anlamı** — `docs/MODULES.md` içinde "ne ne işe yarıyor" kısa özet var.

---

## Kod ve mimari

- **Clean Architecture / DDD** kullanılıyor. Domain (`domain/`) altyapıya bağımlı olmasın; repository ve dış servisler interface (port) üzerinden.
- **Veri erişimi:** `ISupervisorRepository`, `ILearningRepository` gibi domain interface’leri kullanılsın; doğrudan infrastructure’ı domain’e taşımayın.
- **Yeni özellik:** Büyük hedefler `docs/ROADMAP.md`, günlük görevler `docs/TASKS.md` ile uyumlu olsun. Önemli bir şey yaptıysanız `DONE.md`’ye tarih + kısa madde ekleyin (kullanıcı veya siz).

---

## Dil ve hitap

- Kullanıcı (Ramazan) "reis" diye hitap edilmeyi ve samimi bir dil tercih ediyor. Cevap verirken buna uygun olun.

---

Bu dosyayı, yeni bir AI aracı projeye dahil olduğunda veya ortak kurallar değiştiğinde güncelleyin.

*Son güncelleme: 2026-02-06*
