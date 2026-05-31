# Trove Clone

Ursina ile geliştirilmiş voxel oyunu prototipi.

## Kurulum

1. Sanal ortam oluştur:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. Bağımlılıkları yükle:
   ```bash
   pip install -r requirements.txt
   ```

3. Oyunu başlat:
   ```bash
   python src/main.py
   ```

## Test

```bash
pytest tests/
```

## Mimari

| Klasör | Sorumluluk |
|---|---|
| `core/` | Motordan bağımsız saf mantık — dünya verisi, chunk, üretim |
| `render/` | Görsel katman — mesh oluşturma, chunk çizimi |
| `entities/` | Oyuncu ve düşman durumu |
| `systems/` | Savaş, envanter, loot |
| `ui/` | HUD ve arayüz |
| `persistence/` | Kaydet / yükle |
| `config/` | Blok, sınıf ve oyun ayar tanımları |
| `assets/` | Doku, model, ses |
