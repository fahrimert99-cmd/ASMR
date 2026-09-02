"""
YouTube video yayinlama (unlisted/private -> public).

Once "unlisted" olarak yuklenen bir videoyu, incelendikten sonra HERKESE ACIK
(public) yapar. Video ID'sini alir ve yalnizca gizlilik durumunu gunceller.
Kimlik bilgileri youtube_yukle.py ile aynidir (YOUTUBE_TOKEN_JSON / token.json).

Kullanim:
    python scripts/youtube_yayinla.py --id VIDEO_ID
    python scripts/youtube_yayinla.py --id VIDEO_ID --gizlilik unlisted   # geri al
"""
import argparse
import os
import sys

from googleapiclient.discovery import build

# Ayni klasordeki youtube_yukle.py'nin kimlik yukleyicisini tekrar kullan.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from youtube_yukle import kimlik_bilgileri_al  # noqa: E402


def gizlilik_degistir(video_id: str, gizlilik: str = "public") -> str:
    creds = kimlik_bilgileri_al()
    youtube = build("youtube", "v3", credentials=creds)

    # categoryId gibi zorunlu snippet alanlarini kaybetmemek icin once mevcut
    # snippet'i okuyup status ile birlikte tam bir update gonderiyoruz.
    mevcut = youtube.videos().list(part="snippet,status", id=video_id).execute()
    ogeler = mevcut.get("items", [])
    if not ogeler:
        print(f"❌ HATA: Video bulunamadı: {video_id}")
        sys.exit(1)

    snippet = ogeler[0]["snippet"]
    status = ogeler[0].get("status", {})
    status["privacyStatus"] = gizlilik

    youtube.videos().update(
        part="snippet,status",
        body={"id": video_id, "snippet": snippet, "status": status},
    ).execute()

    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"✅ Video gizliliği güncellendi: {gizlilik}")
    print(f"   {url}")

    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        with open(ozet, "a", encoding="utf-8") as f:
            f.write(f"### ✅ Yayın durumu: {gizlilik}\n\n- {url}\n")
    return url


def main():
    p = argparse.ArgumentParser(description="YouTube videosunu yayınla (public yap)")
    p.add_argument("--id", required=True, help="YouTube video ID")
    p.add_argument("--gizlilik", default="public",
                   choices=["public", "unlisted", "private"],
                   help="Hedef gizlilik (varsayılan: public)")
    args = p.parse_args()
    gizlilik_degistir(args.id, args.gizlilik)


if __name__ == "__main__":
    main()
