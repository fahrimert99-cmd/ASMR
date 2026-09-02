"""
YouTube'a yukleme (YouTube Data API v3).
Ilk calistirmada tarayicidan izin ister, token'i config/token.json'a kaydeder.

Hazirlik:
  1. Google Cloud Console'da proje ac, "YouTube Data API v3"u etkinlestir.
  2. OAuth istemcisi (Masaustu) olustur, client_secret.json indir -> config/.
"""
import pickle
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

KAPSAM = ["https://www.googleapis.com/auth/youtube.upload"]


def _servis(ayar: dict):
    token = Path("config/token.json")
    kimlik = None
    if token.exists():
        import google.auth.transport.requests
        from google.oauth2.credentials import Credentials
        kimlik = Credentials.from_authorized_user_file(str(token), KAPSAM)
    if not kimlik or not kimlik.valid:
        akis = InstalledAppFlow.from_client_secrets_file(
            ayar["yukleme"]["client_secret"], KAPSAM)
        kimlik = akis.run_local_server(port=0)
        token.write_text(kimlik.to_json())
    return build("youtube", "v3", credentials=kimlik)


def yukle(video_yolu: str, baslik: str, aciklama: str, ayar: dict,
          etiketler=None) -> str:
    servis = _servis(ayar)
    y = ayar.get("yukleme", {})
    # ASMR/rahatlama icin uygun varsayilanlar: People & Blogs kategorisi,
    # rahatlama etiketleri ve "cocuklara yonelik" KAPALI (aksi halde yorumlar
    # kapanir ve ASMR icerigi cocuk icerigine yanlis siniflandirilirdi).
    # Cocuk icerigi uretiyorsaniz config yukleme.cocuk_icin: true yapin.
    govde = {
        "snippet": {
            "title": baslik,
            "description": aciklama,
            "tags": etiketler or ["asmr", "rahatlama", "uyku",
                                  "relaxing", "sleep", "meditation"],
            "categoryId": str(y.get("kategori_id", "22")),  # 22 = People & Blogs
            "defaultLanguage": "tr",
            "defaultAudioLanguage": "tr",
        },
        "status": {"privacyStatus": y.get("gizlilik", "private"),
                   "selfDeclaredMadeForKids": bool(y.get("cocuk_icin", False))},
    }
    istek = servis.videos().insert(
        part="snippet,status", body=govde,
        media_body=MediaFileUpload(video_yolu, resumable=True),
    )
    yanit = istek.execute()
    return f"https://youtu.be/{yanit['id']}"
