# Teknik Tasarım Dokümanı (TDD)
### BMI4242 — Game Programming / Dönem Projesi

---

## Doküman Başlığı

| Alan | Bilgi |
|---|---|
| **Oyun Adı** | **Trove Clone** — Voxel Tabanlı Aksiyon-RPG |
| **Takım Adı** | *[Takım adınızı buraya yazın]* |
| **Hedef Motor / Çatı** | Python 3.12 + **Ursina 8.3.0** (Panda3D render altyapısı) |

**Takım Üyeleri ve Birincil Rolleri** *(roller projedeki gerçek modüllere göre dağıtılmıştır)*

| Üye | Birincil Rol | Sorumlu olduğu kod |
|---|---|---|
| Arif Can Ekici | Çekirdek Döngü & Voxel Motoru | `core/world`, `core/chunk`, `main` (akış, streaming, fizik) |
| *[İsim Soyisim]* | Prosedürel Üretim Programcısı | `core/generation`, `core/dungeon`, `core/structures` |
| *[İsim Soyisim]* | Render & Meshing Programcısı | `render/mesher`, `render/chunk_renderer` |
| *[İsim Soyisim]* | Oynanış Sistemleri (Savaş/AI/Loot) | `systems/`, `entities/` |
| *[İsim Soyisim]* | UI/UX & Kalıcılık (Persistence) | `ui/`, `persistence/save_manager` |

> Not: Kod tabanı ~7.000 satır Python'dur (40+ modül). Roller örtüşse de her üye en az bir katmanın birincil sahibidir.

---

## 1. Oyun Genel Bakışı

**Asansör Tanıtımı (Elevator Pitch):** Prosedürel üretilmiş, kırılıp inşa edilebilen voxel bir dünyada; sınıf seçip (Savaşçı/Okçu/Büyücü) düşman avlayan, yeraltı zindanlarını ve gökyüzü kalelerini keşfedip boss yenen birinci şahıs bir aksiyon-RPG.

**Temel Mekanikler (Core Mechanics):**
- **Blok etkileşimi:** Sol/sağ tık ile blok kırma ve yerleştirme (raycast tabanlı).
- **Birinci şahıs hareket:** WASD + zıplama/çift zıplama, koşma (Shift), su içinde yüzme — tamamı **özel fizik** ile (motorun hazır controller'ı devre dışı).
- **Savaş:** Yakın dövüş (`F`) + sınıfa özel iki aktif yetenek (`Q`/`E`), bekleme süreli (cooldown).
- **İlerleme:** Düşmandan XP → seviye atlama → can artışı; loot toplama, crafting, ekipman ve tüccardan alışveriş.
- **Keşif:** 5 katlı yeraltı zindanı, yer üstü yapıları, ışınlanma portallı boss arenaları, gece/gündüz döngüsü.

**Kazanma / Kaybetme Koşulları (Win/Loss):**
- **Kaybetme:** Oyuncunun canı 0'a düşünce ölüm ekranı belirir; ~2.5 sn sonra spawn noktasında **yeniden doğar** (kalıcı ölüm yok — sandbox ilerlemesi).
- **Hedef/Kazanma:** Zindan katlarını derinleştikçe artan zorlukta boss'ları yenmek ve yapı arenalarını temizlemek. İlerleme sürekli (endless-progression) bir döngü olarak tasarlanmıştır; sert bir "Oyunu Kazandın" ekranı yerine yenilen her boss bir ara hedeftir.

---

## 2. Yazılım Mimarisi

### 2.1 Üst Düzey Yapı — Katmanlı Mimari + "Veri / Görsel Ayrımı"

Projenin temel mimari ilkesi tek bir cümleyle özetlenir: **veriyi görselden ayır.** Dünya, bellekte saf bir veri yapısıdır; ekranda görünen, bu verinin o anki bir görselleştirmesidir. `core/` katmanı oyun motorunu (Ursina) **hiç tanımaz** ve motor olmadan da çalışıp test edilebilir.

Geleneksel bir OOP hiyerarşisi yerine, **katmanlı (layered) + hafif bileşen (component-style)** bir yaklaşım kullanıldı. Bağımlılıklar tek yöne — dışarıdan içeriye, yani `core`'a doğru — akar; karşılıklı bağımlılık yoktur.

```
src/
├── main.py        → kompozisyon kökü (composition root): her şeyi kurar, mantık tutmaz
├── core/          → MOTORDAN BAĞIMSIZ saf mantık (world, chunk, generation, dungeon, structures)
├── render/        → veriyi mesh'e çevirip ekrana basar (mesher, chunk_renderer)
├── entities/      → oyuncu durumu, düşmanlar, boss, tüccar, sandık
├── systems/       → savaş, envanter, loot, crafting, yetenek, spawn, ekipman, gece/gündüz
├── ui/            → HUD, hotbar, minimap, envanter/crafting/mağaza ekranları
└── persistence/   → JSON kaydet/yükle
config/            → KOD DEĞİL: blok, sınıf ve ayar tanımları (data-driven)
tests/             → saf core mantığının birim testleri (pytest)
```

| Katman | Tek cümlelik sorumluluğu | Neyi bilmez |
|---|---|---|
| **core** | Voxel verisi, chunk'lar, prosedürel üretim | Ekranı, Ursina'yı |
| **render** | Veriyi mesh'e çevirip çizmek, yüz gizleme | Oyun kurallarını |
| **entities** | Oyuncu/düşman durumu, hareket, AI | Çizimin detayını |
| **systems** | Savaş, envanter, loot, yetenek kuralları | Görseli |
| **ui** | HUD, menüler | Mantığın iç işleyişini |
| **persistence** | Dünya/oyuncu diske yaz-oku | Diğer katmanların içini |

### 2.2 Çekirdek Yöneticiler / Kontrolcüler

Tek giriş noktası [`main.py`](src/main.py)'dir; iş yapmaz, sadece sistemleri kurup birbirine bağlar. Çalışma zamanında oyun döngüsü **Ursina'nın `app.run()`** içinde yürür ve her sistem bir `Entity` olarak kendi `update()`/`input()` metoduyla her karede tetiklenir (**Update Method** deseni). Başlıca çalışan sistemler:

- **World** — voxel veri deposu (`get_block`/`set_block`, dünya↔chunk koordinat dönüşümü).
- **TerrainGenerator / DungeonGenerator / StructureGenerator** — chunk'ları doldurur, zindan ve yapıları yerleştirir.
- **ChunkStreamer** — oyuncu yürüdükçe yeni sütunları kuyruğa alıp **kare başına bütçeli** üretir/render eder; menzil dışına çıkanları yok eder.
- **MovementSystem / TerrainPhysics** — yatay duvar çarpışması ve dikey fizik (özel yazıldı; motorun hazır controller'ı `speed=0` ile kapatıldı).
- **SpawnManager / CombatHandler / AbilitySystem** — düşman üretimi, yakın dövüş, aktif yetenekler.
- **BlockInteraction** — raycast ile blok kır/koy ve değişikliği kalıcılığa bildir.
- **HUD / Hotbar / Minimap / *UI** — arayüz; oyun durumunu **callback** ile dinler.

**Modüller arası iletişim — gevşek bağlama (loose coupling):** Sistemler birbirini doğrudan çağırmak yerine **callback/olay** kullanır. Örneğin düşman ölünce `on_death(enemy, type)` tetiklenir; `SpawnManager` bunu yakalayıp loot düşürür ve XP verir — `Enemy` sınıfı loot sistemini hiç tanımaz. Aynı şekilde ekipman değişince `on_change` → HUD güncellenir, sandık açılınca `on_collect` çağrılır. Bu, **Observer** desenidir.

### 2.3 Kullanılan Tasarım Desenleri

| Desen | Nerede | Neden |
|---|---|---|
| **Update Method / Game Loop** | Her sistem `Entity.update()` | Her karede durum ilerletme; motorun döngüsüne tek noktadan bağlanma |
| **Observer (callback)** | `on_death`, `on_change`, `on_collect`, `on_select` | Sistemleri birbirine sıkı bağlamadan haberleştirmek |
| **State Machine** | Ölüm/yeniden doğma, gece/gündüz döngüsü, yetenek cooldown'ları | Zamana bağlı geçişleri (alive→dead→respawn) net yönetmek |
| **Data-Driven / Strategy** | Sınıflar `dataclass` + `config/*.json` | İçeriği koddan ayırmak; yeni blok/sınıf eklemeyi kod değişikliği gerektirmez hâle getirmek |
| **Composition Root** | `main.py` | Tüm bağımlılıkları tek yerde kurup enjekte etmek (dependency injection) |
| **Component** | Düşman gövdesi/gözleri/HP barı ayrı `Entity` | Görsel parçaları bağımsız bileşenlerden kurmak |

---

## 3. Algoritmik Uygulama ve Veri Yapıları

Bu, projenin mühendislik açısından en yoğun bölümüdür. Bilinçli olarak hiçbir hazır oyun-motoru "level editor"ü kullanılmadı; **dünya, çarpışma, üretim ve mesh tamamen elde** yazıldı.

### 3.1 Veri Yapıları

- **Dünya = sözlük (hash map):** `World._chunks`, `(cx, cy, cz) → ChunkData`. Sınırsız dünyayı seyrek (sparse) biçimde tutar; sadece üretilmiş chunk'lar bellekte durur. Dünya↔chunk dönüşümü `divmod(w, chunk_size)` ile O(1).
- **Chunk = NumPy 3B dizi:** Her [`ChunkData`](src/core/chunk.py) `16×16×16` `uint16` bir `numpy` dizisidir. Blok başına 2 bayt, bütün chunk ~8 KB; bitişik bellek sayesinde erişim hızlı ve `is_empty()` tek `np.any` çağrısıyla anlık.
- **Zindan hava kümesi (set):** Zindan boşlukları **önceden hesaplanıp** bir `set[(wx,wy,wz)]` içinde tutulur. Çalışma zamanında "bu blok zindan boşluğu mu?" sorusu **O(1)**'dir (her chunk üretiminde noise yeniden çalıştırılmaz).
- **Mesh ara yapısı:** `MeshData` — `vertices / triangles / uvs / normals / colors` paralel listeleri; doğrudan Ursina `Mesh`'ine beslenir.
- **Koridor planı = graf:** Zindan odaları düğüm, koridorlar kenardır; "en yakın komşu" bağlantısıyla bağlı bir graf kurulur.
- **Envanter/durum:** `block_counts` / `item_counts` sözlükleri; düşmanlar/boss'lar `SpawnManager` içinde liste.

### 3.2 Prosedürel Üretim

**Arazi yüksekliği — çok oktavlı OpenSimplex gürültüsü:** [`TerrainGenerator.get_surface_height`](src/core/generation.py) üç oktav simplex gürültüsünü `1.0 / 0.5 / 0.25` ağırlıklarıyla toplar (fraktal Brownian hareketi benzeri). Ayrı bir düşük frekanslı "biome" gürültüsü dört biyomu (Ova/Çöl/Kar/Orman) belirler. Biyom sınırlarında uçurum oluşmaması için biyom ağırlıkları **smoothstep** (`t·t·(3−2t)`) ile bir geçiş bandında harmanlanır; nihai yükseklik dört biyom yüksekliğinin ağırlıklı ortalamasıdır.

**Su:** Deniz seviyesinin (`y=33`) altındaki çukurlar üretim sırasında su bloğuyla doldurulur.

**Mağaralar — "solucan" tüpleri:** İki bağımsız 3B gürültü alanı `n1, n2` için `n1² + n2² < eşik` koşulu sağlanan voxel'ler oyulur. İki alanın kesişimi, izole boşluklar yerine **birbirine bağlı tünel ağları** üretir.

**Cevher ve ağaçlar — gürültü yerine tamsayı hash:** Her cevher/ağaç için pahalı gürültü çağırmak yerine ucuz bir tamsayı karma kullanılır:
`(wx·374761393 ^ wy·1376312589 ^ wz·2654435761 ^ seed) & 0xFFFF`. Sonuç bir eşikle kıyaslanarak determinist ama "rastgele görünen" dağılım elde edilir (kömür ~%3, demir ~%1.5; ağaçlar ormanda ~%2). Bu, üretimi belirgin biçimde hızlandırır.

**Zindan — graf tabanlı oda/koridor üretimi:** [`DungeonGenerator`](src/core/dungeon.py) 5 katı (`FLOOR_Y = [22,14,6,-4,-14]`) bir ızgara üzerinde olasılıkla oda yerleştirir (derin katlar daha sık ve sıkışık). Sonra:
- **Yatay bağlantı:** Her oda, aynı kattaki **en yakın komşusuna** L-şeklinde (3×3 kesitli) koridorla bağlanır → bağlı bir graf.
- **Dikey bağlantı:** Komşu katlar, eğimi **1:2'yi aşmayan** rampa tünellerle bağlanır (oyuncu zıplamadan yürüyebilir). Adım sayısı `max(|dx|, |dz|, |dy|·2)` ile seçilerek eğim garanti altına alınır.
Tüm boşluklar tek seferde "air set"e oyulur; arazi üretimi bu kümeye bakıp ilgili blokları boşaltır.

### 3.3 Render: Yüz Gizleme (Face Culling) ile Mesh Üretimi

Naif yaklaşımda her küp 12 üçgenle çizilir ve görünmeyen iç yüzler GPU'yu boşa yorar. Bunun yerine [`mesher.build_mesh`](src/render/mesher.py) **sadece komşusu hava (0) olan yüzleri** üretir. Komşu aynı chunk içindeyse diziden, chunk sınırındaysa `neighbor_getter` (dünya `get_block`) ile **chunk'lar arası** bakılır — böylece bitişik chunk yüzeyinde delik/çizgi oluşmaz. Doku yerine **vertex renkleri** kullanılır (blok tipi → renk) ve yüz yönüne göre sabit bir parlaklık çarpanı (`_FACE_DIM`) uygulanarak ucuz bir sahte aydınlatma/AO etkisi verilir. Her chunk **tek bir `Entity`/mesh** olarak çizilir (binlerce küp yerine tek draw call benzeri toplu çizim).

### 3.4 Özel Fizik ve Çarpışma — "yol tarama" (anti-tunneling)

Motorun hazır fiziği yerine voxel verisini doğrudan sorgulayan özel bir sistem yazıldı:
- **Dikey fizik ([`TerrainPhysics`](src/main.py)):** Klasik "yeni y'de blok var mı?" kontrolü yüksek hızda zemini delip geçer (tunneling). Bunun yerine düşüş **yolundaki her bloğu tarayıp** çarpılacak ilk katı yüzeyi bulur. Ayrıca ayak çevresinde 5 sütunluk bir kontrolle kenarda asılı kalma engellenir; su kaldırma kuvveti (buoyancy), çift zıplama, eşik üstü düşüş hızında **düşme hasarı** ve geri-itme (knockback) bu sistemde işlenir.
- **Yatay çarpışma ([`MovementSystem`](src/main.py)):** Hareket **eksen eksen** denenir — önce X, sonra Z. Bir eksende `world.get_block` katı dönerse o eksen iptal edilir; böylece oyuncu duvar boyunca kayabilir, köşeye saplanmaz. Suda yavaşlama ve koşma çarpanları burada uygulanır.

### 3.5 Düşman AI ve Savaş

- **AI (yönelme/seek):** [`Enemy.update`](src/entities/enemy.py) her kare oyuncuya doğru normalize edilmiş bir vektörle ilerler, menzile girince cooldown'lu saldırır, "slow" durum efektiyle yavaşlatılabilir. A\* yerine doğrudan yönelme tercih edildi; çünkü açık voxel arazide hedef genelde görüş hattındadır ve A\*'ın her kare yol hesaplama maliyeti bu ölçekte gereksizdir (bilinçli mimari karar — bkz. §4).
- **Derinliğe göre spawn:** [`SpawnManager`](src/systems/spawn_manager.py) oyuncunun Y yüksekliğine bakıp uygun düşmanı seçer: yüzeyde slime/goblin, sığ zindanda troll, derinde iskelet. Aynı anda en fazla `MAX_ENEMIES = 6` düşman bulunur.
- **Yakın dövüş:** [`CombatHandler`](src/systems/spawn_manager.py) erişim küresi (`REACH = 3.0`) içindeki tüm hedeflere hasar verir (taban hasar + ekipman bonusu) ve hasar sayısı parçacığı gösterir.

### 3.6 Kalıcılık — Delta (fark) Kayıt

[`SaveManager`](src/persistence/save_manager.py) tüm dünyayı diske yazmaz — bu devasa olurdu. Bunun yerine sadece **oyuncunun değiştirdiği blokları** (`"x,y,z": id`) JSON olarak saklar; dünyanın geri kalanı seed'den **determinist** yeniden üretilir. Oyuncu durumu (sınıf, tüketilebilirler, ekipman, gear çantası) `version: 2` formatında ayrıca yazılır. Yükleme önce dünyayı üretir, sonra fark bloklarını üstüne uygular.

---

## 4. Optimizasyon ve Bellek Yönetimi

**Performans darboğazları ve çözümleri:**

| Darboğaz | Çözüm |
|---|---|
| Görünmeyen küp yüzleri | **Yüz gizleme:** yalnız havaya bakan yüzler mesh'e eklenir (iç yüzler hiç üretilmez) |
| Binlerce küp = binlerce draw | Chunk başına **tek mesh entity**; doku yerine vertex rengi → doku bağlama (texture bind) yok |
| Yeni alan üretirken kare donması | **Bütçeli streaming:** `ChunkStreamer` kare başına en çok `GEN_PER_FRAME` sütun üretir; geri kalanı kuyrukta bekler → ani FPS düşüşü yok |
| FPC raycast'inin tüm sahne ağacını gezmesi | `player.traverse_target` boş bir entity'ye yönlendirildi → raycast anında döner |
| Her blokta mesh collider | Collider çoğu chunk'ta **kapalı** (`with_collider=False`); çarpışma zaten `world.get_block` ile çözülüyor |
| Her chunk'ta noise tekrarı | Zindan boşlukları **önceden hesaplanmış set** (O(1) sorgu); cevher/ağaç **tamsayı hash** (noise'suz) |
| Voxel depolama | **NumPy `uint16`** bitişik dizi — kompakt ve hızlı |

**Bellek yönetimi:** Bellek kullanımı **render mesafesiyle sınırlıdır.** Oyuncu hareket ettikçe `ChunkStreamer` hedef kümeyi yeniden hesaplar ve menzil dışındaki chunk renderer'larını `destroy()` ile yok eder; böylece harita ne kadar gezilirse gezilsin yüklü mesh sayısı sabit kalır. Düşmanlar öldüğünde, loot toplandığında ve sandıklar açıldığında ilgili `Entity`'ler yok edilir. Düşman sayısı `MAX_ENEMIES = 6` ile, eşzamanlı boss/loot sayısı yapı/spawn mantığıyla üst sınırlıdır. (Mermi/düşman için açık bir **object pooling** uygulanmadı; bunun nedeni eşzamanlı nesne sayısının düşük tutulması ve düşman üretiminin cooldown'la sınırlanmasıdır — bu, GC baskısını pratikte düşük tutan bilinçli bir basitleştirmedir ve gelecekteki bir optimizasyon adayıdır.)

---

## 5. Versiyon Kontrolü ve İş Akışı

**Git stratejisi — Özellik Dalı (Feature Branch) İş Akışı:** `main` her zaman çalışır durumda tutulur. Her yeni sistem (örn. "zindan üretimi", "yetenek sistemi", "minimap") kendi dalında geliştirilir, çalışır hâle gelince `main`'e birleştirilir; yarım iş `main`'e itilmez. Katmanlı mimari, bu iş bölümünü doğal kılar: iki kişi `render/` ve `systems/` üzerinde aynı anda, çakışmadan çalışabilir çünkü dosya sınırları nettir. Her büyük kilometre taşı bir sürüm etiketiyle (`tag`) işaretlenir; bozulma olursa son çalışan sürüme dönülür.

**Üretilen dosyalar depo dışında:** [`.gitignore`](.gitignore) ile sanal ortam (`venv/`), Python önbelleği (`__pycache__`), oyun kayıtları (`saves/`), log ve IDE/OS çöp dosyaları depodan dışlanır — bunlar depoyu şişirir ve gereksiz çakışma üretir.

**Entegrasyon zorlukları ve çözümleri:**
- **Chunk sınırı dikişleri:** İki kişi `core` (veri) ve `render` (mesh) üzerinde paralel çalışırken, chunk sınırındaki yüzlerin yanlış gizlenmesi görünür "dikiş/delik" yarattı. Çözüm, mesher'a `neighbor_getter` enjekte edip komşu chunk'ın verisine bakmaktı — bu, veri ve render katmanları arasındaki sözleşmeyi netleştirdi.
- **Fizik ↔ streaming yarışı:** Henüz üretilmemiş bir sütunun üzerine düşen oyuncu boşluğa gömülüyordu. Çözüm, `TerrainPhysics`'in yalnızca üretilmiş sütunlarda (`_gen_cols`) çalışması, üretilmemiş sütunda dikey hızı sıfırlamasıydı.
- **Birleştirme disiplini:** "Veri/görsel ayrımı" ilkesi sayesinde çakışmalar büyük ölçüde tek katmanda kaldı; `core/` saf mantık olduğu için birim testleri (`pytest`, 14 test) her birleştirmeden önce regresyonu yakaladı.

---

## Ek: Test Edilebilirlik

`core/` katmanının motordan bağımsız olmasının somut ödülü: ekran açmadan, `pytest` ile chunk veri yönetimi, dünya koordinat dönüşümü ve prosedürel üretim doğrulanabilir ([tests/](tests/) — 14 test). Render ve girdi katmanına test yazılmadı; asıl kazanç **kuralların** doğruluğunu sınamaktır.

---

*Bu doküman oyunun "kaput altı" mühendisliğini anlatır; oyunun hikâyesini/atmosferini değil. Mimari ilke tektir: **veriyi görselden ayır** — sistemin yarısını test edilebilir, diğer yarısını değiştirilebilir kılan budur.*
