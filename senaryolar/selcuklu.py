"""
Senaryo: Buyuk Selcuklu Devleti — Horasan'daki kurulustan (1037) Melikşah
donemindeki en genis sinirlara (1092).

Sinirlar ozet niteligindedir: Anadolu'daki Turk beylikleri ve Anadolu
Selcuklulari, Gurcistan, Karahanlilar ve Cezire emirlikleri "vasal / bagli"
olarak gosterilir. Malazgirt (1071) sonrasi Anadolu'nun fethi 1075'te Iznik'e
ulasan genel ilerleme olarak ozetlenir.
"""
from senaryolar._ortak import b as _b

BASLIK = "BÜYÜK SELÇUKLU DEVLETİ"
ALT_BASLIK = "Horasan'dan Akdeniz'e"
PROJEKSIYON = dict(lon0=52.0, lat0=36.0, lat1=30.0, lat2=42.0)
RENK = (30, 115, 105)
BARUT = False
MUZIK = dict(makam="ussak", kok="D", tohum=5)

YOUTUBE = dict(
    baslik="Büyük Selçuklu Devleti 1037–1092: Dandanakan'dan Malazgirt'e #Shorts",
    aciklama=("Tuğrul ve Çağrı Beylerin Horasan'da kurduğu devlet, Alp Arslan ve Melikşah "
              "döneminde Kaşgar'dan Akdeniz'e uzandı. Büyük Selçuklu'nun yükselişi 20 saniyede."),
    etiketler=["Büyük Selçuklu", "Selçuklu", "Alp Arslan", "Malazgirt", "Melikşah",
               "Tuğrul Bey", "Türk tarihi", "tarih", "harita", "Shorts"],
)

SURE = 20.0

OLAYLAR = [
    dict(t=1.6, yil=1037, baslik="KURULUŞ", alt="Tuğrul ve Çağrı Bey · Merv",
         yer=(61.83, 37.60), ses="kurulus"),
    dict(t=2.9, yil=1040, baslik="DANDANAKAN SAVAŞI", alt="Gazneliler yenildi · devlet ilan edildi",
         yer=(61.50, 37.25), ses="ok"),
    dict(t=4.1, yil=1043, baslik="HAREZM VE REY", alt="Tuğrul Bey · İran'a yayılış",
         yer=(51.43, 35.60), ses="fetih"),
    dict(t=5.3, yil=1048, baslik="PASİNLER SAVAŞI", alt="Bizans'a karşı ilk büyük zafer",
         yer=(41.68, 39.98), ses="savas"),
    dict(t=6.6, yil=1055, baslik="BAĞDAT'A GİRİŞ", alt="Tuğrul Bey · halifenin koruyucusu",
         yer=(44.36, 33.31), ses="fetih"),
    dict(t=7.9, yil=1064, baslik="ANİ'NİN FETHİ", alt="Alp Arslan · Kafkasya seferi",
         yer=(43.57, 40.50), ses="kusatma"),
    dict(t=9.2, yil=1071, baslik="MALAZGİRT ZAFERİ", alt="Alp Arslan · Anadolu'nun kapıları açıldı",
         yer=(42.53, 39.15), ses="ok"),
    dict(t=10.5, yil=1075, baslik="İZNİK", alt="Kutalmışoğlu Süleyman Şah · Anadolu",
         yer=(29.72, 40.43), ses="fetih"),
    dict(t=11.8, yil=1079, baslik="SURİYE VE KUDÜS", alt="Tutuş · Şam",
         yer=(36.29, 33.51), ses="fetih"),
    dict(t=13.4, yil=1089, baslik="MAVERAÜNNEHİR", alt="Melikşah · Semerkant ve Kaşgar",
         yer=(66.97, 39.65), ses="ok"),
    dict(t=15.7, yil=1092, baslik="EN GENİŞ SINIRLAR", alt="Melikşah · Kaşgar'dan Akdeniz'e",
         yer=(51.67, 32.65), ses="final"),
]

BASKENTLER = [(1037, "Merv"), (1043, "Rey"), (1051, "İsfahan")]

SEHIRLER = [
    ("Merv", 61.83, 37.60, 1037, "buyuk"),
    ("Nişabur", 58.80, 36.20, 1038, "kucuk"),
    ("Dandanakan", 61.50, 37.25, 1040, "savas"),
    ("Herat", 62.20, 34.35, 1041, "kucuk"),
    ("Rey", 51.43, 35.60, 1042, "buyuk"),
    ("Pasinler", 41.68, 39.98, 1048, "savas"),
    ("İsfahan", 51.67, 32.65, 1051, "buyuk"),
    ("Tebriz", 46.29, 38.08, 1054, "kucuk"),
    ("Bağdat", 44.36, 33.31, 1055, "buyuk"),
    ("Ani", 43.57, 40.50, 1064, "kucuk"),
    ("Malazgirt", 42.53, 39.15, 1071, "savas"),
    ("Kudüs", 35.23, 31.78, 1073, "kucuk"),
    ("İznik", 29.72, 40.43, 1075, "kucuk"),
    ("Şam", 36.29, 33.51, 1076, "kucuk"),
    ("Semerkant", 66.97, 39.65, 1089, "kucuk"),
    ("Kaşgar", 75.99, 39.47, 1090, "kucuk"),
]

BOLGELER = [
    # ---- 1037: Kuzey Horasan (giriste Merv'den buyur)
    _b("Kuzey Horasan", "d", None,
       [(59.5, 38.5), (61.5, 38.8), (63.5, 38.5), (64.0, 37.5), (63.5, 36.3), (61.5, 35.6),
        (59.5, 35.8), (58.0, 36.5), (58.5, 37.6)],
       tohum=[(61.83, 37.60)], zaman=(0.85, 1.6)),

    # ---- 1037 -> 1043: Horasan, Harezm
    _b("Horasan ve Cürcan", "d", (1038, 1042),
       [(56.0, 37.5), (54.0, 37.0), (55.5, 35.5), (57.5, 33.5), (60.0, 33.8), (62.5, 34.2),
        (64.0, 35.8), (66.0, 36.4), (67.4, 36.8), (66.5, 37.3), (65.0, 38.0), (63.5, 38.5),
        (61.5, 38.8), (59.5, 38.5), (57.5, 38.0)]),
    _b("Harezm", "d", (1042, 1043),
       [(56.0, 38.0), (55.5, 41.5), (56.5, 44.0), (58.5, 45.5), (59.5, 44.5), (61.0, 43.5),
        (62.0, 41.5), (63.8, 39.6), (63.5, 38.5), (61.5, 38.6), (59.5, 38.4), (57.5, 38.0)]),

    # ---- 1043 -> 1055: Cibal, Isfahan-Fars-Kirman-Huzistan, Azerbaycan
    _b("Rey ve Cibal", "d", (1042, 1046),
       [(49.0, 37.6), (49.7, 37.65), (50.6, 37.15), (51.2, 36.85), (53.6, 37.0), (54.0, 37.4),
        (55.5, 35.5), (57.5, 33.5), (55.0, 32.0), (52.0, 32.0), (50.0, 33.0), (47.2, 33.6),
        (45.6, 34.6), (45.3, 35.8), (46.0, 36.6), (48.5, 36.8)]),
    _b("İsfahan, Fars, Kirman", "d", (1048, 1062),
       [(48.5, 34.0), (50.0, 33.0), (52.0, 32.0), (55.0, 32.0), (57.5, 33.5), (60.0, 33.8),
        (60.5, 31.0), (61.5, 29.0), (61.5, 26.5), (58.8, 25.4), (57.6, 25.5), (56.4, 26.65),
        (54.8, 26.3), (52.5, 27.1), (51.3, 27.7), (50.3, 29.3), (48.9, 29.7), (48.3, 30.8),
        (47.5, 32.5), (47.0, 33.5)]),
    _b("Azerbaycan", "d", (1053, 1055),
       [(44.5, 40.0), (43.9, 38.6), (44.0, 37.4), (45.3, 36.9), (46.0, 36.5), (47.5, 36.5), (48.5, 36.8),
        (49.0, 37.6), (49.2, 38.4), (49.4, 39.4), (49.8, 40.5), (49.0, 41.5), (48.5, 41.8),
        (46.5, 41.5), (45.0, 40.8)]),
    _b("Irak", "d", (1054.4, 1055),
       [(43.5, 37.3), (44.6, 37.6), (46.2, 36.7), (46.0, 35.0), (47.0, 34.0), (47.0, 33.5),
        (47.5, 32.5), (48.3, 30.8), (48.8, 29.8), (48.0, 29.6), (46.5, 30.3), (45.0, 31.0),
        (43.5, 32.0), (42.0, 33.5), (41.0, 34.6), (41.5, 36.0), (42.5, 37.2)],
       tohum=[(44.36, 33.31)]),

    # ---- 1055 -> 1064: Cezire (vasal), Ermenistan, Gurcistan (vasal)
    _b("Cezire ve Diyarbakır", "v", (1056, 1060),
       [(37.5, 37.0), (39.0, 36.9), (40.5, 36.0), (41.0, 34.6), (41.5, 36.0), (42.5, 37.2),
        (43.5, 37.5), (42.0, 37.5), (40.5, 37.8), (39.0, 38.3), (38.5, 37.3)],
       dogrudan=(1085, 1087)),
    _b("Ermenistan", "d", (1063, 1064),
       [(41.0, 40.6), (42.0, 41.0), (43.5, 41.2), (45.0, 40.8), (46.5, 39.5), (46.0, 38.9),
        (44.2, 38.9), (43.5, 39.3), (42.5, 39.5), (41.5, 40.0)]),
    _b("Gürcistan", "v", (1067, 1070),
       [(41.6, 41.7), (41.0, 42.6), (40.0, 43.4), (41.5, 43.2), (44.0, 42.8), (46.5, 41.8),
        (46.5, 41.5), (45.0, 40.8), (43.5, 41.2), (42.0, 41.0)]),

    # ---- 1064 -> 1075: Dogu Anadolu, Anadolu (vasal beylikler / Anadolu Selcuklu)
    _b("Doğu Anadolu", "d", (1071, 1073),
       [(38.0, 40.6), (39.5, 40.4), (41.0, 40.6), (41.5, 40.0), (42.5, 39.5), (43.5, 39.3),
        (44.0, 38.5), (43.5, 37.5), (42.0, 37.5), (40.5, 37.8), (39.0, 38.3), (38.0, 39.0)],
       tohum=[(42.53, 39.15)]),
    _b("Van gölü havzası", "d", (1071, 1073),
       [(42.8, 37.2), (45.2, 37.2), (45.2, 39.8), (42.8, 39.8)]),
    _b("Anadolu beylikleri", "v", (1072, 1075),
       [(29.0, 40.9), (29.05, 41.0), (30.5, 41.1), (31.5, 40.9), (33.5, 40.9), (35.5, 40.8),
        (37.0, 40.5), (38.0, 40.6), (38.0, 39.0), (39.0, 38.3), (38.5, 37.3), (37.0, 37.2),
        (35.5, 37.2), (34.0, 37.0), (32.5, 36.8), (31.0, 37.3), (29.5, 37.3), (28.0, 37.8),
        (27.0, 38.4), (26.9, 39.2), (27.5, 40.0), (28.5, 40.3), (29.0, 40.5)]),

    # ---- 1075 -> 1089: Suriye-Filistin, Maveraunnehir (vasal Karahanlilar)
    _b("Suriye ve Filistin", "d", (1071, 1079),
       [(36.0, 36.9), (35.8, 36.0), (35.4, 34.0), (34.6, 32.6), (34.2, 31.3), (34.9, 29.6),
        (35.5, 30.0), (36.5, 31.5), (37.5, 33.0), (38.5, 34.5), (39.5, 35.5), (40.5, 36.0),
        (39.0, 36.9), (37.5, 37.0)]),
    _b("Batı Karahanlılar", "v", (1086, 1089),
       [(61.5, 40.0), (62.0, 41.5), (64.0, 42.5), (66.5, 42.0), (68.5, 42.8), (70.5, 42.0),
        (71.5, 41.5), (72.0, 41.0), (73.5, 40.5), (73.0, 39.5), (71.0, 39.0), (68.5, 37.5),
        (67.3, 37.2), (66.5, 37.3), (65.0, 38.0), (63.5, 38.5), (61.5, 38.8)]),
    _b("Doğu Karahanlılar", "v", (1089.2, 1090.5),
       [(73.5, 40.3), (72.0, 40.9), (71.5, 41.5), (72.0, 43.0), (75.2, 43.0), (76.5, 43.5), (80.0, 44.0),
        (80.5, 43.0), (81.2, 41.6), (82.0, 40.2), (82.0, 38.2), (81.0, 36.6), (79.0, 36.4),
        (77.0, 37.0), (75.0, 37.5), (73.5, 38.5), (73.0, 39.5)]),
]

KAMERA = [
    (0.0, (56.5, 34.0, 66.5, 40.5)),
    (1.6, (57.5, 34.8, 65.5, 39.8)),
    (2.9, (55.0, 33.5, 67.0, 41.0)),
    (4.1, (48.0, 31.0, 67.0, 44.5)),
    (5.3, (38.0, 30.0, 67.0, 45.0)),
    (6.6, (36.0, 28.0, 67.0, 45.0)),
    (7.9, (36.0, 28.0, 68.0, 46.0)),
    (9.2, (33.0, 27.0, 68.0, 46.0)),
    (10.5, (25.0, 27.0, 70.0, 46.0)),
    (11.8, (25.0, 26.0, 70.0, 46.0)),
    (13.4, (25.0, 25.0, 80.0, 47.0)),
    (15.7, (25.0, 24.0, 81.0, 47.5)),
    (20.0, (23.0, 22.5, 83.0, 48.5)),
]

KITALAR = [("ASYA", 62.0, 44.5, 0), ("ANADOLU", 35.2, 38.7, 0)]
