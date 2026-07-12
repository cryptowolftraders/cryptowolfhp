# -*- coding: utf-8 -*-
"""
🐺 WOLF İÇ LİNKLEME SCRIPT'İ  (KATEGORİ AYRIMLI SÜRÜM)
------------------------------------------------------------
/rehber/ klasöründeki tüm HTML sayfaları tarar ve her sayfaya, KENDİ
KATEGORİSİNDEKİ en yakın konulu sayfalara link veren bir "İlgili Yazılar"
bloğu ekler:
    • Kavram makaleleri   →  yalnızca kavram makalelerine linklenir
    • Tarayıcı kılavuzları →  yalnızca tarayıcı kılavuzlarına linklenir

Kategori otomatik bulunur:
    - JSON-LD "TechArticle" içeren sayfa   -> KILAVUZ
    - JSON-LD "Article" içeren sayfa       -> KAVRAM
    - Bulunamazsa dosya adına bakar ("-rehberi" / "tarayici" -> KILAVUZ)
    - Yine emin değilse scriptin başındaki ELLE_KATEGORI listesine bak

Özellikler:
    • Sadece standart Python (kurulum yok, çift tıkla çalışır)
    • Tekrar çalıştırınca blok TEKRARLANMAZ (var olanı yeniler)
    • İlk çalıştırmada .bak yedeği alır
    • Hub sayfaları linklenmez

KULLANIM:
    1. Bu dosyayı /rehber/ klasörünün İÇİNE koy.
    2. Çift tıkla  (veya:  python wolf_ic_link.py)
"""

import os
import re
import glob
import math
import shutil
from collections import Counter

# ─────────────────────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────────────────────
ILGILI_SAYI = 4                       # Sayfa başına link sayısı
YEDEK_AL = True
HUB_DOSYALAR = {"index.html", "tarayicilar.html"}

# Otomatik tahmin yanılırsa dosyayı burada elle sabitle:
#   "dosya.html": "kavram"   veya   "dosya.html": "kilavuz"
ELLE_KATEGORI = {
    # "ornek-sayfa.html": "kilavuz",
}

STOPWORDS = set("""
ve veya ile bir bu şu o da de ki mi mı mu mü için gibi daha çok az en her
nedir demek ne nasıl olan olur ise ya ama fakat ancak yani hem tüm kullanılır
the a an of to in is are and or for with wolf akademi rehber tarayıcı tarayici
""".split())

MARKER = "wolf-related-articles"

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except Exception:
    pass


def metin_temizle(s):
    s = re.sub(r"(?is)<script.*?</script>", " ", s)
    s = re.sub(r"(?is)<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = s.lower()
    s = re.sub(r"[^a-zçğıöşü0-9\s]", " ", s)
    return [k for k in s.split() if len(k) > 2 and k not in STOPWORDS]


def baslik_bul(html):
    m = re.search(r"(?is)<title>(.*?)</title>", html)
    if m:
        t = re.sub(r"\s*[|\-–—]\s*Wolf.*$", "", m.group(1), flags=re.I).strip()
        return t or m.group(1).strip()
    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", html)
    if m:
        return re.sub(r"(?s)<[^>]+>", "", m.group(1)).strip()
    return "Yazı"


def kategori_bul(dosya, html):
    """'kavram' veya 'kilavuz' döndürür."""
    if dosya in ELLE_KATEGORI:
        return ELLE_KATEGORI[dosya]
    low = html.lower()
    if "techarticle" in low:
        return "kilavuz"
    if re.search(r'"@type"\s*:\s*"?article', low):
        return "kavram"
    ad = dosya.lower()
    if "-rehberi" in ad or "tarayici" in ad or "-nasil" in ad:
        return "kilavuz"
    return "kavram"


def blok_temizle(html):
    return re.sub(
        r"(?s)<!--\s*%s:start\s*-->.*?<!--\s*%s:end\s*-->\s*" % (MARKER, MARKER),
        "", html)


def blok_uret(ilgili, kategori):
    baslik = "🐺 İlgili Kılavuzlar" if kategori == "kilavuz" else "🐺 İlgili Yazılar"
    kartlar = [
        '      <a class="wolf-rel-card" href="%s">%s</a>' % (d, b)
        for d, b in ilgili
    ]
    return (
        "\n<!-- %s:start -->\n" % MARKER +
        '<section class="wolf-related" aria-label="İlgili İçerikler">\n'
        "  <style>\n"
        "    .wolf-related{max-width:900px;margin:48px auto;padding:0 20px;}\n"
        "    .wolf-related h2{font-family:'Cinzel',serif;font-weight:600;color:#f5b342;"
        "font-size:1.4rem;margin-bottom:18px;letter-spacing:.5px;}\n"
        "    .wolf-rel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;}\n"
        "    .wolf-rel-card{display:block;padding:16px 18px;background:rgba(45,212,191,.06);"
        "border:1px solid rgba(45,212,191,.25);border-radius:12px;color:#e5e7eb;"
        "text-decoration:none;font-size:.95rem;line-height:1.4;transition:.2s;}\n"
        "    .wolf-rel-card:hover{border-color:#2dd4bf;background:rgba(45,212,191,.12);"
        "box-shadow:0 0 16px rgba(45,212,191,.18);color:#fff;}\n"
        "  </style>\n"
        "  <h2>%s</h2>\n" % baslik +
        '  <div class="wolf-rel-grid">\n' +
        "\n".join(kartlar) +
        "\n  </div>\n</section>\n"
        "<!-- %s:end -->\n" % MARKER
    )


def blok_ekle(html, blok):
    if re.search(r"(?i)</footer>", html):
        return re.sub(r"(?i)</footer>", blok + "</footer>", html, count=1)
    if re.search(r"(?i)</body>", html):
        return re.sub(r"(?i)</body>", blok + "</body>", html, count=1)
    return html + blok


def main():
    dosyalar = sorted(glob.glob("*.html"))
    if not dosyalar:
        print("Bu klasorde .html yok. Scripti /rehber/ icine koy.")
        input("\nCikmak icin Enter...")
        return

    veri = {}
    for d in dosyalar:
        with open(d, "r", encoding="utf-8") as f:
            html = f.read()
        temiz = blok_temizle(html)
        veri[d] = {
            "baslik": baslik_bul(temiz),
            "kelime": Counter(metin_temizle(temiz)),
            "kategori": kategori_bul(d, temiz),
            "raw": html,
        }

    N = len(veri)
    df = Counter()
    for d in veri:
        for k in set(veri[d]["kelime"]):
            df[k] += 1
    idf = {k: math.log((N + 1) / (df[k] + 1)) + 1 for k in df}

    def vektor(d):
        c = veri[d]["kelime"]
        t = sum(c.values()) or 1
        return {k: (c[k] / t) * idf.get(k, 1) for k in c}
    vek = {d: vektor(d) for d in veri}

    def benzerlik(a, b):
        va, vb = vek[a], vek[b]
        ortak = set(va) & set(vb)
        pay = sum(va[k] * vb[k] for k in ortak)
        na = math.sqrt(sum(v * v for v in va.values())) or 1
        nb = math.sqrt(sum(v * v for v in vb.values())) or 1
        return pay / (na * nb)

    kav = [d for d in dosyalar if d not in HUB_DOSYALAR and veri[d]["kategori"] == "kavram"]
    kil = [d for d in dosyalar if d not in HUB_DOSYALAR and veri[d]["kategori"] == "kilavuz"]
    print("Kavram makaleleri: %d   |   Tarayici kilavuzlari: %d\n" % (len(kav), len(kil)))

    degisen = 0
    for d in dosyalar:
        if d in HUB_DOSYALAR:
            continue
        kat = veri[d]["kategori"]
        adaylar = [e for e in dosyalar
                   if e != d and e not in HUB_DOSYALAR and veri[e]["kategori"] == kat]
        skorlar = sorted(((benzerlik(d, e), e) for e in adaylar), reverse=True)
        secilen = [(e, veri[e]["baslik"]) for _, e in skorlar[:ILGILI_SAYI]]
        if not secilen:
            print("[atlandi] %-34s (kategoride baska sayfa yok)" % d)
            continue

        html = veri[d]["raw"]
        if YEDEK_AL and not os.path.exists(d + ".bak"):
            shutil.copy(d, d + ".bak")
        html = blok_temizle(html)
        html = blok_ekle(html, blok_uret(secilen, kat))
        with open(d, "w", encoding="utf-8") as f:
            f.write(html)
        degisen += 1
        etiket = "[KILAVUZ]" if kat == "kilavuz" else "[KAVRAM] "
        print("%s %-30s -> %s" % (etiket, d, ", ".join(e for e, _ in secilen)))

    print("\nTamam! %d sayfa guncellendi." % degisen)
    print("Yedekler .bak uzantisiyla duruyor. Kontrol edip silebilirsin.")
    print("Kategori yanlis cikan sayfa olursa scriptin basindaki ELLE_KATEGORI'ye ekle.")
    input("\nCikmak icin Enter...")


if __name__ == "__main__":
    main()
