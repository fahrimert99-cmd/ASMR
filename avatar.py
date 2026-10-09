"""
Avatar video orkestratoru: "1 Dakikalik Nefes Molasi".

Tek bir avatar gorselinden dikey (9:16, YouTube Shorts uyumlu) 1 dakikalik
rehberli nefes videosu uretir. Avatar izleyiciyle birlikte nefes alir, goz
kirpar; ekrandaki nefes halkasi AL / TUT / VER ritmini gosterir.

    python avatar.py                                # avatar/ profili, 60 sn
    python avatar.py --sure 90                      # daha uzun (dongu sayisi artar)
    python avatar.py --ses-motoru piper             # cevrimdisi Turkce ses
    python avatar.py --gorsel foto.jpg --profil yok # baska gorsel (goz kirpmasiz)
    python avatar.py --yukle                        # bitince YouTube'a yukle

Adimlar: zaman cizelgesi -> seslendirme (edge-tts / Piper) -> ses karisimi
(muzik + can + nefes sesi + ambient) -> kare kare render + ffmpeg kodlama.
"""
import argparse
import sys
from pathlib import Path

from src import KOK, ayarlari_yukle, cikti_klasoru
from src import avatar_senaryo as m_senaryo
from src import avatar_ses as m_ses
from src import avatar_montaj as m_montaj


def _profil_yukle(profil_yolu: str, gorsel: str):
    """Avatar profilini (yaml) ve gorsel yolunu cozer."""
    import yaml

    if profil_yolu and profil_yolu.lower() != "yok":
        yol = Path(profil_yolu)
        if not yol.is_absolute():
            yol = KOK / yol
        profil = yaml.safe_load(yol.read_text(encoding="utf-8")) or {}
        varsayilan_gorsel = yol.parent / profil.get("gorsel", "avatar.jpg")
    else:
        profil, varsayilan_gorsel = {}, None
    gorsel_yolu = Path(gorsel) if gorsel else varsayilan_gorsel
    if gorsel_yolu is None or not gorsel_yolu.exists():
        raise FileNotFoundError(f"Avatar gorseli bulunamadi: {gorsel_yolu}")
    return profil, gorsel_yolu


def main():
    p = argparse.ArgumentParser(description="Avatarli 1 dakikalik nefes molasi videosu")
    p.add_argument("--gorsel", default="", help="Avatar gorseli (bos: profildeki gorsel)")
    p.add_argument("--profil", default="avatar/avatar.yaml",
                   help="Avatar profili (odak, gogus, goz egrileri) ya da 'yok'")
    p.add_argument("--sure", type=float, default=None,
                   help="Video suresi (sn). Bos ise config avatar.sure (60)")
    p.add_argument("--ses-motoru", default="",
                   help="auto | edge | piper | yok (bos ise config avatar.ses_motoru)")
    p.add_argument("--ambient", default="",
                   help="Arka plan ambient tipi: yagmur | okyanus | gece | ... | yok")
    p.add_argument("--yukle", action="store_true", help="Bitince YouTube'a yukle")
    args = p.parse_args()

    ayar = ayarlari_yukle()
    a = ayar.setdefault("avatar", {})
    if args.ses_motoru:
        a["ses_motoru"] = args.ses_motoru
    if args.ambient:
        a["ambient"] = args.ambient
    sure = float(args.sure or a.get("sure", 60))

    profil, gorsel = _profil_yukle(args.profil, args.gorsel)
    c = m_senaryo.nefes_molasi(sure)
    print(f"Avatar videosu  |  gorsel: {gorsel.name}  |  sure: {c.toplam:.0f} sn  "
          f"|  {c.dongu_sayisi} nefes dongusu")

    cikti = cikti_klasoru("avatar-nefes-molasi")

    print("1/4  Replikler seslendiriliyor...")
    motor = m_ses.seslendir(c, ayar, cikti / "ses")
    print(f"     ses motoru: {motor}")

    print("2/4  Ses karisimi (anlatim + muzik + can + nefes + ambient)...")
    ses = m_ses.karistir(c, ayar, cikti / "ses" / "karisim.wav")

    print("3/4  Kareler render ediliyor ve kodlaniyor...")
    video = m_montaj.render(gorsel, profil, c, ses,
                            cikti / "video" / "avatar_nefes_molasi.mp4", ayar,
                            kapak=cikti / "video" / "kapak.jpg")

    baslik = a.get("baslik", "1 Dakikalık Nefes Molası")
    if args.yukle or ayar.get("yukleme", {}).get("aktif"):
        from src import yukleme as m_yukleme
        print("4/4  YouTube'a yukleniyor...")
        url = m_yukleme.yukle(str(video), baslik,
                              f"{baslik}\n\n#nefes #rahatlama #asmr #shorts", ayar)
        print(f"     Yuklendi: {url}")
    else:
        print("4/4  Yukleme atlandi (--yukle ile acabilirsiniz).")

    if not video.exists() or video.stat().st_size == 0:
        raise RuntimeError(f"Islem bitti ama video olusmadi/bos: {video}")
    print(f"\nBITTI ✅  Avatar videosu: {video.resolve()} "
          f"({video.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
