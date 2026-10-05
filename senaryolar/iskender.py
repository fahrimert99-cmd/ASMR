"""
Senaryo: Buyuk Iskender Imparatorlugu — tahta cikistan (MO 336) Babil'deki
olumune (MO 323).

Sinirlar ozet niteligindedir: Korint Birligi'ndeki Yunan sehirleri, Tuna'ya
kadarki Trak boylari, Paflagonya-Kapadokya, Kirene ve Hint kralligi Poros
"vasal / bagli" olarak; satraplıklar dogrudan yonetim olarak gosterilir.
Iskender'in donus yolunda (MO 325) aldigi Asagi Indus, Gedrosya ve Karamanya
en genis sinirlara dahildir.
"""
from senaryolar._ortak import b as _b

BASLIK = "BÜYÜK İSKENDER İMPARATORLUĞU"
ALT_BASLIK = "Makedonya'dan İndus'a On Üç Yıl"
PROJEKSIYON = dict(lon0=48.0, lat0=33.0, lat1=25.0, lat2=42.0)
RENK = (181, 108, 18)
BARUT = False
LEJANT = ("Satraplık (doğrudan yönetim)", "Bağlı devlet / müttefik")
MUZIK = dict(makam="nihavend", kok="A", tohum=3)

YOUTUBE = dict(
    baslik="Büyük İskender İmparatorluğu MÖ 336 – 323: Makedonya'dan İndus'a #Shorts",
    aciklama=("20 yaşında tahta çıkan Makedonya kralı İskender, on üç yılda Pers İmparatorluğu'nu "
              "yıkıp Hindistan'a ulaştı. Büyük İskender'in fetihleri 20 saniyede harita üzerinde."),
    etiketler=["Büyük İskender", "Makedonya", "Pers İmparatorluğu", "Gavgamela", "antik tarih",
               "tarih", "harita", "Shorts"],
)

SURE = 20.0

OLAYLAR = [
    dict(t=1.6, yil=-336, baslik="İSKENDER TAHTTA", alt="Makedonya Kralı · Pella",
         yer=(22.52, 40.76), ses="kurulus"),
    dict(t=2.9, yil=-335, baslik="TRAKYA VE TEB", alt="Tuna seferi · Teb yıkıldı",
         yer=(23.32, 38.32), ses="kusatma"),
    dict(t=4.1, yil=-334, baslik="GRANİKOS SAVAŞI", alt="Asya'ya geçiş · ilk büyük zafer",
         yer=(27.25, 40.25), ses="savas"),
    dict(t=5.3, yil=-333, baslik="İSOS SAVAŞI", alt="Pers kralı III. Dareios kaçtı",
         yer=(36.20, 36.85), ses="savas"),
    dict(t=6.5, yil=-332, baslik="SUR KUŞATMASI", alt="Fenike düştü · Mısır kapıları açıldı",
         yer=(35.20, 33.27), ses="kusatma"),
    dict(t=7.8, yil=-331, baslik="GAVGAMELA SAVAŞI", alt="İskenderiye kuruldu · Babil teslim oldu",
         yer=(43.40, 36.55), ses="savas"),
    dict(t=9.0, yil=-330, baslik="PERSEPOLİS", alt="Ahameniş başkenti alındı",
         yer=(52.89, 29.93), ses="fetih"),
    dict(t=10.3, yil=-329, baslik="BAKTRİA VE SOGDİYANA", alt="Orta Asya seferi · Semerkant",
         yer=(66.97, 39.65), ses="ok"),
    dict(t=11.6, yil=-327, baslik="HİNDİSTAN'A GİRİŞ", alt="Hindukuş aşıldı · Taksila",
         yer=(72.80, 33.75), ses="fetih"),
    dict(t=13.4, yil=-326, baslik="HİDASPES SAVAŞI", alt="Kral Poros ve savaş filleri",
         yer=(73.60, 32.90), ses="savas"),
    dict(t=15.7, yil=-323, baslik="EN GENİŞ SINIRLAR", alt="Babil'de ölüm · henüz 32 yaşında",
         yer=(44.42, 32.54), ses="final"),
]

BASKENTLER = [(-336, "Pella"), (-324, "Babil")]

SEHIRLER = [
    ("Pella", 22.52, 40.76, -336, "buyuk"),
    ("Atina", 23.73, 37.98, -336, "kucuk"),
    ("Teb", 23.32, 38.32, -335, "savas"),
    ("Granikos", 27.25, 40.25, -334, "savas"),
    ("Sardes", 28.04, 38.49, -334, "kucuk"),
    ("Gordion", 31.99, 39.65, -333, "kucuk"),
    ("İsos", 36.20, 36.85, -333, "savas"),
    ("Sur", 35.20, 33.27, -332, "savas"),
    ("İskenderiye", 29.92, 31.20, -331, "buyuk"),
    ("Gavgamela", 43.40, 36.55, -331, "savas"),
    ("Babil", 44.42, 32.54, -331, "buyuk"),
    ("Susa", 48.25, 32.19, -331, "kucuk"),
    ("Persepolis", 52.89, 29.93, -330, "buyuk"),
    ("Ekbatana", 48.52, 34.80, -330, "kucuk"),
    ("Baktra", 66.90, 36.76, -329, "kucuk"),
    ("Semerkant", 66.97, 39.65, -329, "kucuk"),
    ("Taksila", 72.80, 33.75, -327, "kucuk"),
    ("Hidaspes", 73.60, 32.90, -326, "savas"),
]

BOLGELER = [
    # ---- MO 336: Makedonya + Filip'in mirasi (giriste buyur)
    _b("Makedonya", "d", None,
       [(20.6, 41.2), (20.9, 42.0), (22.3, 42.3), (23.6, 42.0), (24.8, 41.5), (24.9, 40.9),
        (24.5, 40.0), (23.4, 39.9), (23.3, 39.2), (22.8, 38.85), (22.0, 38.9), (21.2, 39.5),
        (20.9, 40.4)],
       tohum=[(22.52, 40.76)], zaman=(0.85, 1.6)),
    _b("Korint Birliği", "v", None,
       [(20.7, 38.7), (22.0, 38.9), (22.8, 38.85), (23.3, 39.2), (24.0, 39.1), (24.75, 38.6),
        (25.8, 37.4), (25.8, 36.4), (23.0, 36.1), (21.3, 36.5), (20.5, 37.6), (20.4, 38.4)],
       zaman=(1.0, 1.6)),

    # ---- MO 336 -> 335: Trakya (guney dogrudan, Tuna'ya kadar kuzey bagli)
    _b("Güney Trakya", "d", (-336, -335.4),
       [(23.9, 41.6), (23.8, 42.2), (25.0, 42.6), (27.0, 42.7), (27.9, 42.6), (28.1, 42.0), (28.9, 41.3),
        (29.0, 41.05), (28.0, 40.9), (27.0, 40.6), (26.2, 40.3), (25.5, 40.75), (24.9, 40.9)]),
    _b("Trak boyları (Tuna'ya kadar)", "v", (-335.6, -335),
       [(22.3, 42.3), (22.4, 43.0), (22.6, 44.2), (24.0, 43.7), (26.0, 43.8), (27.5, 44.1),
        (28.6, 44.3), (28.2, 43.2), (27.9, 42.6), (27.0, 42.7), (25.0, 42.6), (23.6, 42.0)]),

    # ---- MO 335 -> 334/333: Kucuk Asya
    _b("Batı ve Güney Anadolu", "d", (-334, -333.4),
       [(26.1, 40.0), (26.4, 40.2), (26.7, 40.4), (27.3, 40.5), (28.6, 40.45), (29.4, 40.3),
        (30.2, 39.9), (31.5, 39.6), (32.6, 39.9), (33.5, 39.5), (34.8, 38.0), (34.2, 37.25),
        (32.6, 37.0), (32.0, 36.5), (30.5, 36.2), (29.3, 36.1), (28.2, 36.6), (27.4, 36.62), (26.9, 37.0),
        (26.1, 38.3), (25.9, 39.2), (26.0, 39.7)],
       tohum=[(27.25, 40.25)]),
    _b("Paflagonya ve Kapadokya", "v", (-333.6, -333),
       [(32.6, 39.9), (32.3, 41.3), (32.5, 41.9), (35.3, 42.2), (36.6, 41.6), (36.5, 40.5),
        (36.5, 39.0), (35.0, 37.8), (33.5, 38.0), (33.5, 39.5)]),

    # ---- MO 333 -> 332: Kilikya, Suriye, Fenike, Kibris
    _b("Kilikya ve Suriye", "d", (-333.05, -332.7),
       [(31.8, 36.6), (32.4, 37.2), (33.5, 37.4), (34.3, 37.7), (35.0, 37.9), (36.5, 37.4), (37.9, 37.0),
        (38.5, 36.0), (38.0, 35.0), (37.0, 34.2), (35.7, 34.4), (35.4, 34.0), (35.5, 34.5),
        (35.7, 36.2), (35.0, 36.5), (33.5, 35.9), (32.6, 35.85)],
       tohum=[(36.20, 36.85)]),
    _b("Fenike ve Filistin", "d", (-332.75, -332),
       [(35.4, 34.0), (35.7, 34.4), (37.0, 34.2), (37.0, 33.5), (36.5, 32.0), (35.9, 30.5),
        (35.0, 29.5), (34.2, 31.3), (34.0, 31.6), (34.8, 32.8)]),
    _b("Kıbrıs", "d", (-333, -332.5),
       [(32.2, 34.5), (34.7, 34.5), (34.7, 35.75), (32.2, 35.75)]),

    # ---- MO 332 -> 331: Misir, Kirene, Mezopotamya
    _b("Mısır", "d", (-332, -331.6),
       [(25.2, 31.9), (29.0, 31.6), (32.3, 31.6), (34.5, 31.3), (35.0, 29.55), (34.5, 27.9),
        (34.0, 27.0), (35.0, 24.0), (35.6, 23.0), (32.0, 23.0), (29.5, 23.2), (25.0, 23.5),
        (25.0, 29.5)],
       tohum=[(32.55, 31.04)]),
    _b("Kirene", "v", (-331.6, -331.3),
       [(19.0, 29.8), (21.0, 30.4), (23.5, 30.8), (25.2, 31.0), (25.2, 31.9), (23.0, 33.0),
        (21.5, 33.2), (20.0, 32.6), (19.5, 31.2), (19.0, 30.5)]),
    _b("Mezopotamya ve Susiana", "d", (-331.35, -331),
       [(37.9, 37.0), (39.5, 37.4), (41.5, 37.4), (43.0, 37.3), (44.5, 37.2), (45.2, 36.0),
        (45.8, 34.5), (46.5, 33.2), (47.8, 32.4), (48.8, 32.6), (49.5, 31.5), (49.3, 30.2),
        (48.0, 29.9), (46.5, 30.5), (45.0, 31.0), (43.5, 32.3), (42.0, 34.0), (40.5, 34.6),
        (38.6, 35.5), (38.0, 35.0), (38.5, 36.0)],
       tohum=[(43.40, 36.55)]),

    # ---- MO 331 -> 330: Pers, Med, Hirkanya, Partya
    _b("Pers ve Med", "d", (-330.9, -330.05),
       [(44.5, 37.2), (45.0, 38.5), (47.0, 39.4), (48.8, 38.4), (49.7, 37.65), (50.6, 37.15), (51.2, 36.85),
        (53.5, 36.9), (55.5, 36.8), (56.5, 35.5), (55.5, 33.5), (54.5, 31.5), (54.5, 28.5),
        (55.0, 26.4), (52.5, 27.1), (51.3, 27.7), (50.3, 29.3), (49.4, 30.2), (49.5, 31.5), (48.8, 32.6),
        (47.8, 32.3), (46.5, 33.2), (45.8, 34.5), (45.2, 36.0)]),

    # ---- MO 330 -> 327: Areia, Drangiana, Arakosya, Baktria, Sogdiana
    _b("Doğu İran ve Baktria", "d", (-330.05, -327.6),
       [(55.5, 36.8), (58.0, 37.9), (61.0, 38.6), (63.5, 40.6), (66.5, 40.6), (69.8, 40.6),
        (70.8, 39.6), (71.6, 37.2), (71.2, 35.8), (69.8, 34.6), (68.5, 33.0), (67.3, 31.0),
        (66.0, 29.9), (63.5, 29.6), (61.0, 29.5), (58.5, 30.3), (56.5, 33.0), (55.5, 33.5),
        (56.5, 35.5)]),

    # ---- MO 327 -> 326: Gandhara, Poros kralligi
    _b("Gandhara", "d", (-327.2, -326.6),
       [(69.8, 34.6), (71.2, 35.8), (72.5, 35.6), (73.5, 34.5), (73.6, 33.0), (72.5, 32.5),
        (71.0, 32.5), (70.5, 33.5), (68.5, 33.0)],
       tohum=[(70.5, 34.4)]),
    _b("Poros krallığı", "v", (-326.3, -326),
       [(73.5, 34.5), (74.5, 34.2), (75.6, 32.3), (75.5, 31.3), (74.0, 30.8), (72.8, 31.5),
        (72.5, 32.5), (73.6, 33.0)],
       tohum=[(73.60, 32.90)]),

    # ---- MO 326 -> 323: donus yolu — Asagi Indus, Gedrosya, Karamanya
    _b("Aşağı İndus", "d", (-325.8, -325.2),
       [(67.3, 31.0), (68.5, 33.0), (70.5, 33.5), (72.3, 32.7), (72.8, 31.5), (71.5, 29.0),
        (70.5, 27.0), (69.8, 25.5), (68.5, 23.8), (66.8, 24.8), (66.5, 26.5), (67.5, 28.5),
        (66.0, 29.9)]),
    _b("Gedrosya ve Karamanya", "d", (-325.2, -324.6),
       [(66.0, 29.9), (67.6, 28.5), (66.6, 26.5), (66.8, 24.8), (61.5, 25.0), (57.5, 25.5), (56.4, 26.65),
        (54.8, 26.3), (54.5, 28.5), (54.5, 31.5), (55.5, 33.5), (56.5, 33.0), (58.5, 30.3),
        (61.0, 29.5), (63.5, 29.6)]),
]

KAMERA = [
    (0.0, (19.5, 38.5, 26.0, 42.5)),
    (1.6, (20.5, 39.0, 24.5, 41.6)),
    (2.9, (19.5, 37.0, 29.5, 44.5)),
    (4.1, (19.0, 35.0, 34.0, 44.0)),
    (5.3, (21.0, 33.5, 40.0, 43.5)),
    (6.5, (22.0, 28.0, 42.0, 42.0)),
    (7.8, (20.0, 23.0, 52.0, 42.0)),
    (9.0, (20.0, 22.0, 60.0, 43.0)),
    (10.3, (20.0, 22.0, 73.0, 45.0)),
    (11.6, (20.0, 20.0, 80.0, 45.0)),
    (13.4, (20.0, 19.0, 80.0, 45.0)),
    (15.7, (19.0, 18.0, 80.0, 45.5)),
    (20.0, (17.0, 16.0, 82.0, 47.0)),
]

KITALAR = [("AVRUPA", 22.0, 46.5, 0), ("ASYA", 60.0, 44.5, 0), ("AFRİKA", 24.0, 20.5, 0)]
