# Tshark (Wireshark) PATH Ayarı – Windows

Scout Stealth modu paket yakalamak için **tshark** kullanır. Kurulumdan sonra `tshark` komutu tanınmıyorsa PATH'e ekleyin.

## 1. PATH'e Ekleme (Kalıcı)

1. **Windows tuşu + R** → `sysdm.cpl` yazıp Enter.
2. **Gelişmiş** sekmesi → **Ortam Değişkenleri**.
3. **Kullanıcı değişkenleri** bölümünde **Path**'i seç → **Düzenle**.
4. **Yeni** → şunu yapıştır: `C:\Program Files\Wireshark`
5. **Tamam** ile kapat.

## 2. Doğrulama

**Yeni** bir PowerShell veya CMD açın (eski pencereler eski PATH’i kullanır), sonra:

```powershell
tshark --version
```

Sürüm bilgisi geliyorsa PATH doğru demektir.

## 3. Scout Backend

Backend’i bu **yeni** terminalde başlatın; böylece tshark PATH’te olur ve Stealth capture çalışır.

```powershell
cd C:\Users\erama\Scout\backend
.\scout\Scripts\Activate.ps1
$env:PYTHONPATH = "C:\Users\erama\Scout\backend\src"
python -m uvicorn scout.main:app --host 127.0.0.1 --port 8000
```

## Hızlı Test (PATH eklemeden)

Sadece test için geçici olarak:

```powershell
$env:Path += ";C:\Program Files\Wireshark"
tshark --version
```

Bu sadece o oturumda geçerlidir; kalıcı için yukarıdaki “PATH'e Ekleme” adımlarını uygulayın.
