"""Generate localized PSP XMB graphics (ICON0.PNG, PIC0.PNG, SAVEDATA.PNG) and chyuikanki_PSP.GIM."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS  # noqa: E402

sys.path.insert(0, SCRIPTS)
import gim  # noqa: E402

FONTS_DIR = ROOT / "fonts"
FONT_BOLD = FONTS_DIR / "MPLUS1p-Bold.ttf"
FONT_REG = FONTS_DIR / "MPLUS1p-Regular.ttf"
PCE_TITLE_LOGO = ROOT.parent / "benkei-gaiden-pce" / "work" / "qa" / "p7_en" / "title_logo" / "final.png"


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


def _v_blend(im: Image.Image, x0: int, y0: int, x1: int, y1: int) -> None:
    """Fill [x0..x1, y0..y1) with vertical linear blend between rows y0-1 and y1."""
    px = im.load()
    for x in range(x0, x1):
        top = px[x, y0 - 1]
        bot = px[x, y1]
        for y in range(y0, y1):
            t = (y - y0 + 1) / (y1 - y0 + 1)
            px[x, y] = tuple(round(u + (v - u) * t) for u, v in zip(top, bot))


def make_icon0(orig_png: bytes, title_logo_path: Path | None = None) -> bytes:
    """Rebuild 80x80 HuCARD ICON0.PNG / SAVEDATA.PNG using English BENKEI GAIDEN shrine logo art."""
    src_art = title_logo_path or (ROOT / "tools" / "fixtures" / "manual_shots" / "title_logo.png")
    if not src_art.is_file():
        src_art = PCE_TITLE_LOGO
    assert src_art.is_file(), f"missing title artwork: {src_art}"

    orig = Image.open(io.BytesIO(orig_png)).convert("RGB")
    assert orig.size == (80, 80), f"expected 80x80 ICON0, got {orig.size}"
    orig_px = orig.load()

    # Extract the bright sunset torii banner + BENKEI GAIDEN crimson calligraphy (256x144 -> 60x60 pillar/cropped)
    art_src = Image.open(src_art).convert("RGB")
    # Crop centered 200x200 square around the logo + shrine torii (original 256x239: logo spans y=46..170)
    art_sq = Image.new("RGB", (200, 200), (0, 0, 0))
    crop = art_src.crop((28, 36, 228, 186))  # 200x150
    art_sq.paste(crop, (0, 25))
    art_60 = art_sq.resize((60, 60), Image.Resampling.LANCZOS)

    out = orig.copy()
    out.paste(art_60, (14, 10))
    out_px = out.load()

    # Preserve the circular silver/white HuCARD finger tab overlapping the left artwork edge (cx=9.5, cy=39.5, r=10.3)
    for y in range(28, 52):
        for x in range(14, 22):
            if (x - 9.5) ** 2 + (y - 39.5) ** 2 <= 10.3**2:
                out_px[x, y] = orig_px[x, y]

    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def make_pic0(orig_png: bytes, title: str = "Benkei Gaiden") -> bytes:
    """Translate 310x180 XMB info card PIC0.PNG while preserving rounded-corner alpha and badges."""
    orig = Image.open(io.BytesIO(orig_png)).convert("RGBA")
    assert orig.size == (310, 180), f"expected 310x180 PIC0, got {orig.size}"
    rgb = orig.convert("RGB")

    # Clear Japanese title (BENKEI GAIDEN kanji) and 3-line PSN notice using vertical gradient infill
    _v_blend(rgb, 60, 22, 228, 50)
    _v_blend(rgb, 23, 67, 296, 106)

    d = ImageDraw.Draw(rgb)
    shadow = (150, 150, 150)
    f_title = _font(19, True)
    d.text((66, 36), title, font=f_title, fill=shadow, anchor="lm")
    d.text((64, 34), title, font=f_title, fill=(0, 0, 0), anchor="lm")

    f_note = _font(9, True)
    lines = (
        "This title can be played on PSP® and PS3®.",
        "For how to download it to PSP® and PS3® and more,",
        "see the official PlayStation®Network website.",
    )
    for i, line in enumerate(lines):
        y = 75 + 12 * i
        d.text((27, y + 1), line, font=f_note, fill=shadow, anchor="lm")
        d.text((26, y), line, font=f_note, fill=(0, 0, 0), anchor="lm")

    out = rgb.convert("RGBA")
    out.putalpha(orig.getchannel("A"))
    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def make_chyuikanki_gim(orig_gim: bytes) -> bytes:
    """Translate 480x272 copyright/distribution notice screen in chyuikanki_PSP.GIM."""
    imgs = gim.parse(orig_gim)
    assert len(imgs) == 1
    img = imgs[0]
    assert (img.w, img.h) == (480, 272), f"unexpected GIM size {(img.w, img.h)}"
    w, h, rows = gim.to_rgba(orig_gim, img)

    im = Image.frombytes("RGBA", (w, h), b"".join(rows))
    # Clear Japanese header + furigana (x>=130, y<58) and body block (y>=55), keeping [! triangle icon] at x=104..128
    d = ImageDraw.Draw(im)
    d.rectangle((130, 0, 479, 58), fill=(0, 0, 0, 255))
    d.rectangle((0, 55, 479, 271), fill=(0, 0, 0, 255))

    white = (255, 255, 255, 255)
    d.text((137, 39), "Notice", font=_font(22, True), fill=white, anchor="lm")

    f_body = _font(11, True)
    paragraphs = [
        ("All rights relating to this game software and its packaging", 74),
        ("are reserved by the copyright holder.", 90),
        ("Distributing or transmitting this software over the Internet", 112),
        ("without permission is an illegal act violating Article 113,", 128),
        ("Paragraph 1 of the Copyright Act.", 144),
        ("Under the revised Copyright Act effective January 2010,", 166),
        ("knowingly downloading illegally distributed software is also", 182),
        ("unlawful and not exempt as private-use reproduction.", 198),
        ("Thank you for your understanding and cooperation.", 224),
    ]
    for line, y in paragraphs:
        assert f_body.getlength(line) <= 416, f"chyuikanki line too wide: {line}"
        d.text((34, y), line, font=f_body, fill=white, anchor="lm")

    new_raw = im.tobytes()
    out_rows = [new_raw[y * w * 4 : (y + 1) * w * 4] for y in range(h)]
    re_gim = gim.encode(orig_gim, img, out_rows)
    assert len(re_gim) == len(orig_gim)
    return re_gim


def main() -> None:
    prev = ROOT / "work" / "gfx_preview"
    prev.mkdir(parents=True, exist_ok=True)
    unp = ROOT / "work" / "unpacked"

    icon = make_icon0((unp / "content" / "SAVEDATA.PNG").read_bytes(), PCE_TITLE_LOGO)
    (prev / "ICON0.png").write_bytes(icon)

    pic = make_pic0((unp / "iso" / "PSP_GAME" / "PIC0.PNG").read_bytes())
    (prev / "PIC0.png").write_bytes(pic)

    g_bytes = make_chyuikanki_gim((unp / "content" / "chyuikanki_PSP.GIM").read_bytes())
    imgs = gim.parse(g_bytes)
    w, h, rows = gim.to_rgba(g_bytes, imgs[0])
    Image.frombytes("RGBA", (w, h), b"".join(rows)).save(prev / "chyuikanki.png")
    print(f"Wrote previews to {prev}")


if __name__ == "__main__":
    main()
