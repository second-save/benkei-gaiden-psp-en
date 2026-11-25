"""Translate the 18 PSP PC Engine Archives digital manual pages (480x248 RGB PNG).

CLI:
    python3.14 -X utf8 tools/manual.py SRC_DIR OUT_DIR [PAGE...]

Writes OUT_DIR/psp_NNN.png and OUT_DIR/cmp_NNN.png (original stacked above English).
Library API: PAGES (dict[int, list]), page(p: int, png: bytes) -> bytes.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_REG = ROOT / "fonts" / "MPLUS1p-Regular.ttf"
FONT_BOLD = ROOT / "fonts" / "MPLUS1p-Bold.ttf"
FIXTURES = ROOT / "tools" / "fixtures" / "manual_shots"

# Colors sampled from NPJJ30035 manual assets
WHITE = (255, 255, 255)
INK = (45, 45, 45)
BLACK = (20, 20, 20)
MUTED = (80, 80, 80)
RED = (204, 0, 0)
ORANGE = (240, 130, 0)
ORANGE_TXT = (232, 118, 0)
HUDSON_BLUE = (0, 86, 168)
GRAY_CELL = (137, 137, 137)
GRAY_LIGHT = (220, 221, 221)
GRAY_BOX = (220, 221, 221)
BEZEL_GRAY = (114, 113, 113)
INFO_BG = (246, 247, 247)
BADGE_ON = (137, 137, 137)
BADGE_OFF = (212, 212, 212)
PINK_BOX = (245, 76, 146)

_FONTS: dict[tuple[bool, float], ImageFont.FreeTypeFont] = {}


def _font(size: float, bold: bool) -> ImageFont.FreeTypeFont:
    key = (bool(bold), float(size))
    f = _FONTS.get(key)
    if f is None:
        path = FONT_BOLD if bold else FONT_REG
        f = ImageFont.truetype(str(path), size=size)
        _FONTS[key] = f
    return f


# --- Declarative page primitives ------------------------------------------------


def C(x0: int, y0: int, x1: int, y1: int, col: tuple[int, int, int] = WHITE):
    return ("C", x0, y0, x1, y1, col)


def V(x0: int, y0: int, x1: int, y1: int, sx: int | None = None):
    """Fill (x0,y0,x1,y1) by tiling vertical column `sx` (default x1-2) horizontally."""
    return ("V", x0, y0, x1, y1, sx)


def H(x0: int, y0: int, x1: int, y1: int, sy: int | None = None):
    """Fill (x0,y0,x1,y1) by tiling horizontal row `sy` (default y0) vertically."""
    return ("H", x0, y0, x1, y1, sy)


def P(x0: int, y0: int, x1: int, y1: int):
    """Restore original pixels from `orig` inside (x0,y0,x1,y1)."""
    return ("P", x0, y0, x1, y1)


def X(x0: int, y0: int, x1: int, y1: int):
    """Erase (x0,y0,x1,y1) by linear interpolation between orig columns x0-1 and x1 per row."""
    return ("X", x0, y0, x1, y1)


def PCircle(cx: int, cy: int, r: int):
    """Restore a circular badge from `orig` (for the p01 orange PC Engine seal)."""
    return ("PCircle", cx, cy, r)


def Paste(sx0: int, sy0: int, sx1: int, sy1: int, dx: int, dy: int):
    """Cut (sx0,sy0,sx1,sy1) from `orig` and paste at (dx, dy)."""
    return ("Paste", sx0, sy0, sx1, sy1, dx, dy)


def I(name: str, x0: int, y0: int, x1: int, y1: int):
    """Paste fixture screenshot resized with LANCZOS into (x0,y0,x1,y1)."""
    return ("I", name, x0, y0, x1, y1)


def R(x0: int, y0: int, x1: int, y1: int, outline: tuple[int, int, int], width: int = 1):
    """Draw rectangle outline."""
    return ("R", x0, y0, x1, y1, outline, width)


def B(x0: int, y0: int, x1: int, y1: int, txt: str, active: bool):
    """Draw rounded character availability badge (`Ki`, `Sb`, `Sy`, `Be`)."""
    return ("B", x0, y0, x1, y1, txt, active)


def T(
    x: int,
    y: int,
    text: str,
    size: float = 11.0,
    bold: bool = False,
    color: tuple[int, int, int] = INK,
    align: str = "left",
    lh: float | None = None,
    max_w: int | None = None,
):
    return ("T", x, y, text, size, bold, color, align, lh, max_w)


def HDR(title: str):
    """Clear top title bar (preserving bottom bevel) and draw page title."""
    return [V(16, 9, 445, 27, sx=458), T(18, 9, title, 14.5, True, INK)]


# --- Shared table / card builders ----------------------------------------------


def _table_rows(
    x_name0: int,
    x_name1: int,
    x_desc0: int,
    x_desc1: int,
    rows: list[tuple[int, int, str, str]],
    name_size: float = 10.5,
    desc_size: float = 10.0,
) -> list:
    ops: list = []
    for y0, y1, name, desc in rows:
        ops.append(C(x_name0, y0, x_name1, y1, GRAY_CELL))
        ops.append(C(x_desc0, y0, x_desc1, y1, WHITE))
        ops.append(T((x_name0 + x_name1) // 2, (y0 + y1) // 2 - 7, name, name_size, True, WHITE, align="center"))
        n_lines = desc.count("\n") + 1
        lh = desc_size * 1.25
        ty = (y0 + y1) // 2 - round((n_lines * lh) / 2) + 1
        ops.append(T(x_desc0 + 4, ty, desc, desc_size, False, INK, lh=lh))
    return ops


def _jutsu_cards(cards: list[tuple[int, int, str, str, bool, bool]]) -> list:
    ops: list = []
    cw, ch = 138, 47
    for x0, y0, title, desc, ki, sy in cards:
        ops.append(C(x0 + 1, y0 + 1, x0 + cw - 1, y0 + 14, GRAY_CELL))
        ops.append(C(x0 + 1, y0 + 15, x0 + cw - 1, y0 + ch - 1, WHITE))
        ops.append(T(x0 + 5, y0 + 1, title, 10.5, True, WHITE))
        ops.append(T(x0 + 5, y0 + 17, desc, 9.2, False, INK, lh=12.0))
        ops.append(B(x0 + 101, y0 + 29, x0 + 117, y0 + 45, "Ki", ki))
        ops.append(B(x0 + 119, y0 + 29, x0 + 135, y0 + 45, "Sy", sy))
    return ops


def _equip_col(x_gray0: int, x_gray1: int, badges_x0: int, ys: list[int], rows: list[tuple[str, tuple[bool, bool, bool, bool]]]) -> list:
    ops: list = []
    chars = ("Ki", "Sb", "Sy", "Be")
    for idx, (name, flags) in enumerate(rows):
        y0, y1 = ys[idx], ys[idx + 1]
        ops.append(C(x_gray0, y0 + 1, x_gray1, y1, GRAY_CELL))
        ops.append(C(badges_x0 - 1, y0 + 1, badges_x0 + 65, y1, WHITE))
        ops.append(T((x_gray0 + x_gray1) // 2, y0 + 4, name, 9.5, True, WHITE, align="center"))
        for c_i, ch in enumerate(chars):
            bx0 = badges_x0 + c_i * 16
            ops.append(B(bx0, y0 + 3, bx0 + 15, y0 + 19, ch, flags[c_i]))
    return ops


# --- Page Definitions -----------------------------------------------------------

PAGES: dict[int, list[Any]] = {
    1: [
        I("title_logo.png", 20, 55, 178, 173),
        PCircle(36, 40, 25),
        C(60, 32, 166, 48, BEZEL_GRAY),
        T(62, 33, "PC Engine Archives", 9.5, True, WHITE),
        C(66, 206, 121, 234, BEZEL_GRAY),
        T(93, 211, "Manual", 13.0, True, WHITE, align="center"),
        V(212, 14, 462, 50, sx=455),
        T(219, 21, "Benkei Gaiden", 17.5, True, INK),
        C(205, 55, 470, 112, WHITE),
        T(
            208,
            57,
            "An RPG set in Kamakura-era Japan, where demons\n"
            "run rampant. Unravel the mystery of Kijaku's birth\n"
            "and defeat the true enemy!",
            9.3,
            False,
            INK,
            lh=14.0,
        ),
        C(298, 118, 376, 136, WHITE),
        T(337, 120, "Software Info", 10.0, True, INK, align="center"),
        # Info table rows (left col bg INFO_BG, right col bg WHITE)
        C(208, 140, 312, 154, INFO_BG),
        C(314, 140, 465, 154, WHITE),
        T(260, 140, "Genre", 9.5, True, INK, align="center"),
        T(320, 140, "Role-Playing", 9.5, False, INK),
        C(208, 155, 312, 186, INFO_BG),
        C(350, 155, 465, 186, WHITE),
        T(260, 164, "Players", 9.5, True, INK, align="center"),
        T(359, 156, "1 Player", 9.5, False, INK),
        T(359, 172, "1 Player", 9.5, False, INK),
        C(208, 187, 312, 202, INFO_BG),
        C(314, 187, 465, 202, WHITE),
        T(260, 188, "Platform", 9.5, True, INK, align="center"),
        T(320, 188, "PC Engine (HuCARD)", 9.5, False, INK),
        C(208, 203, 312, 218, INFO_BG),
        C(314, 203, 465, 218, WHITE),
        T(260, 204, "Publisher", 9.5, True, INK, align="center"),
        T(320, 204, "SUNSOFT", 9.5, False, INK),
        C(208, 219, 312, 234, INFO_BG),
        C(314, 219, 465, 234, WHITE),
        T(260, 220, "Orig. Release", 9.2, True, INK, align="center"),
        T(320, 220, "December 1989", 9.5, False, INK),
    ],
    2: [
        C(16, 6, 468, 243, WHITE),
        P(18, 36, 35, 51),
        P(18, 110, 35, 125),
        T(20, 8, "Important Health Information", 13.0, True, INK),
        T(38, 37, "WARNING   Photosensitive Seizures Caused by Light", 11.5, True, BLACK),
        T(
            20,
            55,
            "A very small percentage of individuals may experience epileptic seizures or blackouts\n"
            "when exposed to flashing lights or patterns on a screen. Consult a doctor before\n"
            "playing if you or anyone in your family has an epileptic condition or seizure history.",
            9.5,
            False,
            BLACK,
            lh=13.0,
        ),
        T(38, 111, "CAUTION   Stop Playing Immediately If You Feel Unwell", 11.5, True, BLACK),
        T(
            20,
            129,
            "Stop playing immediately and consult a doctor if you experience any of the above,\n"
            "headache, dizziness, nausea, fatigue, motion-sickness symptoms, or discomfort or\n"
            "pain in your eyes, ears, hands, arms, or feet. Resume only after consulting a doctor.",
            9.5,
            False,
            BLACK,
            lh=13.0,
        ),
        T(
            20,
            183,
            "■ Play in a well-lit room and keep a safe distance from the screen.\n"
            "■ Avoid playing when tired or lacking sleep.\n"
            "■ For your health, take a 15-minute break every hour of play.\n"
            "■ Stop playing at once if you begin to feel unwell during play.",
            9.5,
            False,
            BLACK,
            lh=14.5,
        ),
    ],
    3: [
        C(16, 8, 468, 115, WHITE),
        T(20, 9, "Usage Precautions", 13.0, True, INK),
        T(20, 44, "● This software is exclusively for PSP® (PlayStation®Portable).", 11.0, True, BLACK),
        T(
            20,
            68,
            "● Always update the PSP® (PlayStation®Portable) system software to the\n"
            "   latest version before use.",
            11.0,
            True,
            BLACK,
            lh=17.0,
        ),
    ],
    4: [
        *HDR("Playing on PSP® (PlayStation®Portable) ①"),
        H(16, 40, 464, 58, sy=41),
        T(20, 42, "Please note the following when playing this title on PSP®", 10.5, True, INK),
        C(18, 60, 462, 90, WHITE),
        T(23, 64, "■ Peripherals for PSP® (PlayStation®Portable) are not supported.", 10.0, False, INK),
        H(16, 111, 464, 129, sy=112),
        T(20, 113, "About the System Menu", 10.5, True, INK),
        C(18, 132, 462, 200, WHITE),
        T(20, 133, "Press the", 10.0, False, INK),
        Paste(70, 134, 85, 142, 68, 137),
        T(87, 133, "button during play to open the System Menu.", 10.0, False, INK),
        T(
            20,
            154,
            "From the System Menu, you can view the Manual, Save (Suspend), Load (Resume),\n"
            "change the Screen Size, and toggle Backup RAM Autosave ON or OFF.",
            10.0,
            False,
            INK,
            lh=17.0,
        ),
    ],
    5: [
        *HDR("Playing on PSP® (PlayStation®Portable) ②"),
        H(16, 40, 464, 58, sy=41),
        T(20, 42, "About Soft Reset", 10.5, True, INK),
        C(18, 63, 462, 102, WHITE),
        T(
            20,
            64,
            "Hold the START button and press SELECT during gameplay to perform a soft reset.",
            10.0,
            False,
            INK,
        ),
        C(26, 95, 431, 116, GRAY_BOX),
        T(30, 98, "■ Note that unsaved progress is lost when performing a soft reset.", 10.0, False, INK),
        H(16, 132, 464, 150, sy=133),
        T(20, 134, "About Rapid-Fire", 10.5, True, INK),
        C(18, 154, 450, 171, WHITE),
        T(20, 156, "This title supports rapid-fire input. The mapped buttons are listed below.", 10.0, False, INK),
        C(25, 176, 84, 200, GRAY_LIGHT),
        P(26, 181, 41, 195),
        T(44, 181, "Button", 10.0, True, INK),
        C(86, 176, 211, 200, WHITE),
        P(89, 181, 103, 195),
        T(106, 181, "Rapid-Fire", 10.0, False, INK),
        C(25, 202, 84, 227, GRAY_LIGHT),
        P(26, 208, 41, 222),
        T(44, 208, "Button", 10.0, True, INK),
        C(86, 202, 211, 227, WHITE),
        P(89, 208, 103, 222),
        T(106, 208, "Rapid-Fire", 10.0, False, INK),
    ],
    6: [
        *HDR("In-Game Button Labels"),
        C(16, 30, 464, 86, WHITE),
        T(
            20,
            32,
            "PC Engine Archives faithfully reproduces original PC Engine releases, so in-game text\n"
            "may refer to the PC Engine controller buttons. They map to PSP® (PlayStation®Portable)\n"
            "buttons as shown in the diagram below.",
            9.5,
            False,
            INK,
            lh=14.0,
        ),
        H(16, 84, 170, 102, sy=85),
        T(20, 86, "Button Mapping Diagram", 10.0, True, INK),
        # Left top: START -> RUN
        C(15, 109, 119, 125, ORANGE),
        T(67, 110, "START Button", 10.5, True, WHITE, align="center"),
        C(15, 131, 119, 146, GRAY_LIGHT),
        T(67, 131, "RUN Button", 10.0, True, INK, align="center"),
        C(15, 148, 119, 161, (133, 133, 133)),
        T(67, 148, "In-Game Name", 9.0, True, WHITE, align="center"),
        # Left bottom: SELECT -> SELECT
        C(15, 177, 119, 193, ORANGE),
        T(67, 178, "SELECT Button", 10.5, True, WHITE, align="center"),
        C(15, 199, 119, 214, GRAY_LIGHT),
        T(67, 199, "SELECT Button", 10.0, True, INK, align="center"),
        C(15, 216, 119, 229, (133, 133, 133)),
        T(67, 216, "In-Game Name", 9.0, True, WHITE, align="center"),
        # Right top: ○ -> I
        C(366, 109, 465, 125, ORANGE),
        Paste(398, 111, 411, 124, 381, 111),
        T(398, 110, "Button", 10.5, True, WHITE),
        C(366, 131, 465, 146, GRAY_LIGHT),
        T(415, 131, "I Button", 10.0, True, INK, align="center"),
        C(366, 148, 465, 161, (133, 133, 133)),
        T(415, 148, "In-Game Name", 9.0, True, WHITE, align="center"),
        # Right bottom: × -> II
        C(366, 177, 465, 193, ORANGE),
        Paste(398, 179, 411, 192, 381, 179),
        T(398, 178, "Button", 10.5, True, WHITE),
        C(366, 199, 465, 214, GRAY_LIGHT),
        T(415, 199, "II Button", 10.0, True, INK, align="center"),
        C(366, 216, 465, 229, (133, 133, 133)),
        T(415, 216, "In-Game Name", 9.0, True, WHITE, align="center"),
    ],
    7: [
        *HDR("Saving (Suspend Save)"),
        C(16, 32, 336, 122, WHITE),
        T(
            18,
            34,
            "While this title launches from the Memory Stick™ under Game,\n"
            "save files are stored in the Saved Data Utility.",
            9.5,
            False,
            INK,
            lh=15.0,
        ),
        T(
            18,
            78,
            "Settings and current progress can be stored in up to 5 save\n"
            "slots from the System Menu.",
            9.5,
            False,
            INK,
            lh=15.0,
        ),
        # XMB screenshot inset labels (erase by horizontal interpolation of the blue background)
        X(372, 74, 397, 82),
        T(384, 73, "Game", 7.0, True, WHITE, align="center"),
        X(396, 88, 454, 101),
        T(397, 90, "Saved Data Utility", 6.3, False, WHITE),
        # Gray note box (interior only; original border kept)
        C(26, 146, 455, 233, GRAY_BOX),
        T(
            28,
            148,
            "■ Saving each Suspend file requires at least 700 KB of free space on a Memory Stick Duo™\n"
            "   or Memory Stick PRO Duo™.\n"
            "■ Save data created on PSP® cannot be used on PlayStation®3, and save data created\n"
            "   on PlayStation®3 cannot be used on PSP®.\n"
            "■ Only Backup RAM Data can be transferred between PSP® and PlayStation®3.",
            8.8,
            False,
            INK,
            lh=16.5,
        ),
    ],
    8: [
        *HDR("Controls"),
        # L Button (header only)
        C(54, 45, 97, 60, ORANGE),
        P(29, 46, 54, 59),
        T(56, 46, "Button", 10.5, True, WHITE),
        # D-Pad
        C(25, 107, 103, 123, ORANGE),
        T(64, 108, "D-Pad", 10.5, True, WHITE, align="center"),
        C(25, 124, 103, 154, WHITE),
        T(28, 126, "Move /\nSelect Command", 9.0, False, ORANGE_TXT, lh=12.0),
        # Analog Pad
        C(25, 178, 103, 194, ORANGE),
        T(64, 179, "Analog Stick", 10.2, True, WHITE, align="center"),
        C(25, 195, 103, 225, WHITE),
        T(28, 197, "Move /\nSelect Command", 9.0, False, ORANGE_TXT, lh=12.0),
        # SELECT
        C(150, 197, 270, 213, ORANGE),
        T(210, 198, "SELECT Button", 10.5, True, WHITE, align="center"),
        C(150, 214, 270, 233, WHITE),
        T(210, 217, "Reorder Party", 10.0, False, ORANGE_TXT, align="center"),
        # START
        C(309, 197, 392, 213, ORANGE),
        T(350, 198, "START Button", 10.5, True, WHITE, align="center"),
        C(309, 214, 392, 233, WHITE),
        T(350, 217, "Start", 10.0, False, ORANGE_TXT, align="center"),
        # Triangle (header only)
        C(261, 36, 304, 52, ORANGE),
        P(246, 37, 260, 51),
        T(262, 37, "Button", 10.5, True, WHITE),
        # Square (header only)
        C(261, 58, 304, 74, ORANGE),
        P(246, 59, 260, 73),
        T(262, 59, "Button", 10.5, True, WHITE),
        # Circle
        C(356, 58, 459, 74, ORANGE),
        Paste(381, 59, 395, 73, 376, 59),
        T(394, 59, "Button", 10.5, True, WHITE),
        C(356, 75, 459, 121, WHITE),
        T(360, 79, "Confirm / Open\nCommand Window", 9.5, False, ORANGE_TXT, lh=13.5),
        # Cross
        C(356, 136, 459, 152, ORANGE),
        Paste(381, 137, 395, 151, 376, 137),
        T(394, 137, "Button", 10.5, True, WHITE),
        C(356, 153, 459, 185, WHITE),
        T(360, 155, "Cancel /\nView Status", 9.5, False, ORANGE_TXT, lh=13.5),
    ],
    9: [
        *HDR("Starting the Game"),
        I("title_menu.png", 17, 37, 144, 132),
        C(150, 32, 464, 226, WHITE),
        T(154, 36, "Press the START button on the title screen.", 10.5, False, INK),
        T(154, 82, "■ New Game", 11.0, True, ORANGE_TXT),
        T(166, 100, "Start a brand-new journey from the beginning.", 10.0, False, INK),
        T(154, 125, "■ Continue", 11.0, True, ORANGE_TXT),
        T(
            166,
            143,
            "Resume from where you left off.\n"
            "Select Password to enter a recorded password,\n"
            "or Save RAM to load from your saved data file.",
            10.0,
            False,
            INK,
            lh=16.0,
        ),
    ],
    10: [
        *HDR("How to Play"),
        C(16, 32, 330, 154, WHITE),
        C(16, 154, 464, 234, WHITE),
        T(
            18,
            34,
            "In the Kamakura period, a wise monk named Hogen\n"
            "foresees an invasion from the Demon Realm. Taking\n"
            "in Kijaku, a boy of mysterious power with no kin, he\n"
            "settles at Rinsho-ji Temple in Tsukumo Village.\n"
            "Years later, having endured Hogen's harsh training,\n"
            "Kijaku faces a sudden calamity that sparks his quest.",
            9.3,
            False,
            INK,
            lh=13.2,
        ),
        T(
            18,
            118,
            "Defeat demons to grow stronger, and visit towns\n"
            "and villages to gather clues and buy gear or items.",
            9.3,
            False,
            INK,
            lh=13.2,
        ),
        T(
            18,
            155,
            "If an ally's HP reaches 0, they fall in battle. Visit a shrine and pay a donation to Revive\n"
            "them. If the entire party falls, you are returned to the last shrine you visited\n"
            "(and if you were aboard a boat, it returns to the nearest pier to that shrine).",
            9.3,
            False,
            INK,
            lh=14.0,
        ),
    ],
    11: [
        *HDR("Screen Layout"),
        H(16, 37, 464, 55, sy=38),
        T(20, 39, "Screen Overview", 10.0, True, INK),
        I("status_full.png", 17, 75, 175, 186),
        I("battle_party.png", 173, 74, 324, 186),
        C(14, 60, 330, 74, WHITE),
        C(14, 74, 173, 75, WHITE),
        R(93, 119, 171, 157, PINK_BOX, width=1),
        # Cut pink circled numbers ①..⑪ from orig & place beside the English UI features
        Paste(96, 73, 107, 84, 102, 75),    # 1 Name (Kijaku)
        Paste(132, 73, 143, 84, 160, 75),   # 2 Level (Lv 15)
        Paste(80, 92, 91, 103, 84, 97),     # 3 HP
        Paste(149, 100, 160, 111, 163, 115),# 4 MP
        Paste(49, 145, 60, 156, 66, 141),   # 5 Equipment
        Paste(49, 169, 60, 180, 18, 168),   # 6 Sen
        Paste(115, 141, 126, 152, 82, 125), # 7 Stats
        Paste(187, 69, 198, 80, 180, 63),   # 1 Name (Kijaku battle)
        Paste(173, 88, 184, 99, 176, 94),   # 8 Battle HP/MP
        Paste(244, 117, 255, 128, 262, 110),# 9 Enemy
        Paste(202, 161, 213, 172, 228, 166),# 10 Commands
        Paste(272, 161, 283, 172, 305, 160),# 11 Enemy Window
        C(75, 188, 175, 205, WHITE),
        C(250, 188, 326, 205, WHITE),
        T(124, 190, "Status Screen", 10.5, True, INK, align="center"),
        T(282, 190, "Battle Screen", 10.5, True, INK, align="center"),
        # Right legend
        C(357, 73, 466, 224, WHITE),
        C(357, 138, 406, 156, WHITE),
        C(357, 189, 406, 207, WHITE),
        Paste(405, 141, 420, 155, 405, 141),  # 6 badge (legend clear above erased it)
        Paste(405, 191, 420, 205, 405, 191),  # 10 badge
        T(359, 74, "Character Name", 9.0, False, INK),
        T(359, 91, "Level", 9.0, False, INK),
        T(359, 108, "Current / Max HP", 9.0, False, INK),
        T(359, 125, "Current / Max MP", 9.0, False, INK),
        T(359, 142, "Gear", 9.0, False, INK),
        T(422, 142, "Money", 9.0, False, INK),
        T(359, 159, "Stats", 9.0, False, INK),
        T(359, 176, "Current HP / MP", 9.0, False, INK),
        T(359, 193, "Enemy", 9.0, False, INK),
        T(422, 193, "Commands", 8.5, False, INK),
        T(359, 210, "Enemy Window", 9.0, False, INK),
    ],
    12: [
        *HDR("Commands"),
        C(17, 36, 230, 53, WHITE),
        C(245, 36, 460, 53, WHITE),
        T(17, 37, "■ Field Commands", 11.0, True, ORANGE_TXT),
        T(245, 37, "■ Battle Commands", 11.0, True, ORANGE_TXT),
        *_table_rows(
            18,
            61,
            62,
            234,
            [
                (56, 83, "Talk", "Face an adjacent person and talk."),
                (85, 99, "Stats", "View your party's status."),
                (101, 129, "Equip", "Equip or discard weapons and\narmor."),
                (131, 145, "Jutsu", "Cast Jutsu techniques."),
                (147, 175, "Items", "Use or discard items in your\ninventory."),
                (177, 204, "Check", "Search the ground in front of the\nparty leader."),
            ],
            name_size=10.5,
            desc_size=9.3,
        ),
        *_table_rows(
            246,
            289,
            290,
            462,
            [
                (56, 70, "Fight", "Attack with equipped weapon."),
                (72, 86, "Jutsu", "Cast Jutsu techniques."),
                (88, 116, "Flee", "Escape battle with the party\non your turn if successful."),
                (118, 132, "Item", "Use an item."),
            ],
            name_size=10.5,
            desc_size=9.3,
        ),
    ],
    13: [
        *HDR("Jutsu ①"),
        C(16, 30, 464, 84, WHITE),
        T(
            18,
            32,
            "Spending MP to heal or unleash powerful attacks is called Jutsu. Kijaku and Sayaka can\n"
            "learn new Jutsu as they level up. A technique cannot be used if your MP is too low.",
            9.5,
            False,
            INK,
            lh=13.5,
        ),
        *_jutsu_cards(
            [
                (17, 86, "Soul Break", "Blasts one enemy with a\nshockwave.", True, False),
                (171, 86, "Lightning", "Strikes one enemy with\nlightning.", True, False),
                (325, 86, "Frost Chain", "Strikes one enemy with\nice.", True, False),
                (17, 135, "Flame Arc", "Strikes one enemy with\nfire.", True, False),
                (171, 135, "Soul Surge", "Blasts all enemies with a\nshockwave.", False, True),
                (325, 135, "Frost Ring", "Strikes all enemies with\nice.", False, True),
                (17, 184, "Flame Ring", "Strikes all enemies with\nfire.", False, True),
                (171, 184, "Goku-Muten", "Banishes all enemies\nexcept bosses.", False, True),
            ]
        ),
        C(324, 184, 464, 232, WHITE),
        B(325, 187, 341, 204, "Ki", True),
        T(344, 188, "...Usable by Kijaku", 9.5, False, INK),
        B(325, 208, 341, 225, "Sy", True),
        T(344, 209, "...Usable by Sayaka", 9.5, False, INK),
    ],
    14: [
        *HDR("Jutsu ②"),
        *_jutsu_cards(
            [
                (17, 37, "Heal", "Slightly restores one\nally's HP.", True, True),
                (171, 37, "Full Heal", "Greatly restores one\nally's HP.", True, True),
                (325, 37, "Grand Heal", "Fully restores one\nally's HP.", False, True),
                (17, 86, "Revive", "Revives one fallen ally\n(not in battle).", False, True),
                (171, 86, "Purify", "Cures one ally's poison\n(not in battle).", True, True),
                (325, 86, "Raise Might", "Raises the party's Attack\nfor 1 turn.", False, True),
                (17, 135, "Halt Strike", "Raises the party's Guard\nfor 1 turn.", True, False),
                (171, 135, "Seal Jutsu", "Seals all enemies' Jutsu.", True, True),
                (325, 135, "Smokescreen", "Makes escape easier\nfrom non-boss foes.", False, True),
                (17, 184, "Swift Step", "Walk faster for a time\n(not in battle).", False, True),
                (171, 184, "Holy Step", "No encounters for a time\n(not in battle).", True, False),
            ]
        ),
        C(324, 195, 464, 234, WHITE),
        T(326, 201, "Many other Jutsu\nappear in the game.", 9.5, False, INK, lh=14.0),
    ],
    15: [
        *HDR("Equipment"),
        C(17, 36, 464, 53, WHITE),
        T(17, 37, "■ Weapons", 10.5, True, ORANGE_TXT),
        T(168, 37, "■ Armor", 10.5, True, ORANGE_TXT),
        T(320, 37, "■ Gear", 10.5, True, ORANGE_TXT),
        *_equip_col(
            18,
            94,
            95,
            [55, 76, 97, 118, 139, 160, 181, 202],
            [
                ("Hex Staff", (True, False, False, False)),
                ("Sword", (True, True, True, False)),
                ("Naginata", (False, False, False, True)),
                ("Steel Staff", (True, True, False, True)),
                ("Demon Blade", (False, True, False, False)),
                ("Dragon Tail", (False, False, True, False)),
                ("Bane Sword", (True, False, False, False)),
            ],
        ),
        *_equip_col(
            169,
            245,
            246,
            [55, 76, 97, 118, 139, 160, 181, 202],
            [
                ("Apron", (True, False, True, False)),
                ("Monk Robe", (True, True, False, True)),
                ("Plume Veil", (False, False, True, False)),
                ("Bamboo Mail", (True, True, False, False)),
                ("Chainmail", (False, True, False, True)),
                ("Ward Veil", (False, False, True, False)),
                ("Iron Armor", (True, True, False, True)),
            ],
        ),
        *_equip_col(
            321,
            397,
            398,
            [55, 76, 97, 118, 139, 160, 181, 202],
            [
                ("Bracer", (True, True, False, False)),
                ("Bamboo Cuff", (True, False, False, False)),
                ("Silk Shawl", (False, False, True, False)),
                ("Guard Hood", (True, False, True, False)),
                ("Iron Helm", (True, True, False, True)),
                ("Prism Shawl", (False, False, True, False)),
                ("Seal Band", (False, True, False, False)),
            ],
        ),
        C(16, 206, 464, 240, WHITE),
        B(18, 206, 33, 222, "Ki", True),
        T(36, 207, "...Kijaku can equip", 9.0, False, INK),
        B(152, 206, 167, 222, "Sb", True),
        T(170, 207, "...Saburo can equip", 9.0, False, INK),
        B(18, 224, 33, 240, "Sy", True),
        T(36, 225, "...Sayaka can equip", 9.0, False, INK),
        B(152, 224, 167, 240, "Be", True),
        T(170, 225, "...Benkei can equip", 9.0, False, INK),
        T(290, 225, "Many other items appear in-game.", 9.0, False, INK),
    ],
    16: [
        *HDR("Items"),
        *_table_rows(
            18,
            94,
            95,
            314,
            [
                (52, 71, "Salve", "Slightly restores HP."),
                (73, 92, "Great Salve", "Greatly restores HP."),
                (94, 113, "Antidote", "Cures one ally's poison (not in battle)."),
                (115, 134, "Realm Elixir", "Revives one fallen ally (not in battle)."),
                (136, 155, "Ward Incense", "No encounters for a time (not in battle)."),
                (157, 176, "Echo Mirror", "Returns to the last village with an inn."),
                (178, 197, "Dream Lens", "Warps to the Capital."),
                (199, 218, "Calm Flute", "Escapes a cave back to the surface."),
            ],
            name_size=9.5,
            desc_size=9.5,
        ),
        C(322, 48, 462, 92, WHITE),
        T(324, 52, "Many other items\nappear in the game.", 9.5, False, INK, lh=14.0),
    ],
    17: [
        *HDR("Saving to Backup RAM"),
        C(16, 32, 464, 68, WHITE),
        T(
            18,
            34,
            "This title supports Backup RAM. Data is saved separately as Backup RAM Data\n"
            "and can be copied to and used on PlayStation®3.",
            9.5,
            False,
            INK,
            lh=15.0,
        ),
        C(21, 73, 460, 108, GRAY_BOX),
        T(
            24,
            75,
            "■ Saving Backup RAM Data requires about 200 KB of free space on your storage media.\n"
            "■ Ordinary Save Data also includes Backup RAM information.",
            9.0,
            False,
            INK,
            lh=15.5,
        ),
        I("shrine_save.png", 18, 125, 146, 220),
        H(152, 125, 464, 140, sy=126),
        T(155, 126, "About Saving", 10.0, True, INK),
        C(146, 141, 466, 232, WHITE),
        T(
            155,
            146,
            "To save, speak with a shrine priest, choose\n"
            "Password -> Save RAM, then pick a file slot.\n"
            "Saving to a slot that already holds data will\n"
            "overwrite it. Choosing Password -> Password\n"
            "displays your password instead.",
            9.4,
            False,
            INK,
            lh=15.0,
        ),
    ],
    18: [
        C(120, 8, 360, 25, (74, 74, 74)),
        T(240, 9, "Contact Information", 12.0, True, WHITE, align="center"),
        C(16, 34, 238, 107, GRAY_BOX),
        T(19, 36, "● Hudson User Support Center", 9.5, True, INK),
        T(32, 51, "0570-00-4622", 14.0, True, RED),
        T(163, 55, "(Navi-Dial)", 8.0, False, INK),
        T(19, 73, "● If Navi-Dial is unavailable:", 9.5, True, INK),
        T(32, 87, "011-821-7015", 14.0, True, RED),
        C(246, 36, 457, 107, GRAY_BOX),
        T(
            248,
            38,
            "◆ We cannot answer questions about\n"
            "   game strategy.\n"
            "◆ Hours: 12:00 - 17:30\n"
            "   (closed weekends and holidays)\n"
            "◆ Please check the number carefully\n"
            "   before dialing.",
            8.2,
            False,
            INK,
            lh=11.5,
        ),
        C(238, 120, 380, 145, WHITE),
        T(241, 120, "Hudson Soft Co., Ltd.", 11.5, True, INK),
        T(241, 134, "http://www.hudson.co.jp/", 8.5, False, MUTED),
        C(46, 198, 420, 217, WHITE),
        T(
            48,
            200,
            "is a registered trademark of Hudson Soft Co., Ltd. and NEC BIGLOBE, Ltd.",
            8.5,
            False,
            INK,
        ),
        C(8, 217, 472, 246, WHITE),
        T(
            17,
            220,
            "This product uses DynaFont from DynaComware Corporation.\n"
            "DynaFont is a registered trademark of DynaComware Taiwan Inc.",
            8.2,
            False,
            INK,
            lh=10.5,
        ),
        T(463, 229, "All rights reserved.", 8.2, True, INK, align="right"),
    ],
}


# --- Renderer ------------------------------------------------------------------


def render(orig: Image.Image, ops: list[Any]) -> Image.Image:
    im = orig.convert("RGB")
    draw = ImageDraw.Draw(im)
    for op in ops:
        kind = op[0]
        if kind == "C":
            _, x0, y0, x1, y1, col = op
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=col)
        elif kind == "V":
            _, x0, y0, x1, y1, sx = op
            src_x = x1 - 2 if sx is None else sx
            strip = orig.crop((src_x, y0, src_x + 1, y1))
            for x in range(x0, x1):
                im.paste(strip, (x, y0))
        elif kind == "H":
            _, x0, y0, x1, y1, sy = op
            src_y = y0 if sy is None else sy
            strip = orig.crop((x0, src_y, x1, src_y + 1))
            for y in range(y0, y1):
                im.paste(strip, (x0, y))
        elif kind == "P":
            _, x0, y0, x1, y1 = op
            im.paste(orig.crop((x0, y0, x1, y1)), (x0, y0))
        elif kind == "X":
            _, x0, y0, x1, y1 = op
            opx = orig.load()
            px = im.load()
            span = x1 - x0 + 1
            for y in range(y0, y1):
                a, b = opx[x0 - 1, y], opx[x1, y]
                for x in range(x0, x1):
                    t = (x - x0 + 1) / span
                    px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
        elif kind == "PCircle":
            _, cx, cy, r = op
            opx = orig.load()
            px = im.load()
            w, h = im.size
            for y in range(max(0, cy - r), min(h, cy + r + 1)):
                for x in range(max(0, cx - r), min(w, cx + r + 1)):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                        px[x, y] = opx[x, y]
        elif kind == "Paste":
            _, sx0, sy0, sx1, sy1, dx, dy = op
            im.paste(orig.crop((sx0, sy0, sx1, sy1)), (dx, dy))
        elif kind == "I":
            _, name, x0, y0, x1, y1 = op
            shot = Image.open(FIXTURES / name).convert("RGB")
            shot = shot.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
            im.paste(shot, (x0, y0))
        elif kind == "R":
            _, x0, y0, x1, y1, outline, width = op
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=outline, width=width)
        elif kind == "B":
            _, x0, y0, x1, y1, txt, active = op
            col = BADGE_ON if active else BADGE_OFF
            draw.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=3, fill=col)
            f = _font(8.5, True)
            bb = draw.textbbox((0, 0), txt, font=f)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            tx = (x0 + x1 - tw) // 2 - bb[0]
            ty = (y0 + y1 - th) // 2 - bb[1]
            draw.text((tx, ty), txt, font=f, fill=WHITE)
        elif kind == "T":
            _, x, y, text, size, bold, color, align, lh, max_w = op
            f = _font(size, bold)
            step = int(round(lh)) if lh is not None else int(round(size * 1.3))
            lines = text.split("\n")
            cy = y
            for line in lines:
                lx = x
                if align != "left":
                    bb = draw.textbbox((0, 0), line, font=f)
                    lw = bb[2] - bb[0]
                    if align == "center":
                        lx = x - lw // 2
                    elif align == "right":
                        lx = x - lw
                draw.text((lx, cy), line, font=f, fill=color)
                cy += step
        else:
            raise ValueError(f"unknown op: {kind}")
    return im


def page(p: int, png: bytes) -> bytes:
    """Render manual page `p` (1..18) onto original PNG bytes and return RGB PNG bytes."""
    orig = Image.open(io.BytesIO(png)).convert("RGB")
    out = render(orig, PAGES[p])
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) < 2:
        print("usage: manual.py SRC_DIR OUT_DIR [PAGE...]", file=sys.stderr)
        return 2
    src_dir, out_dir = Path(args[0]), Path(args[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = [int(a) for a in args[2:]] if args[2:] else sorted(PAGES)
    for p in wanted:
        raw = (src_dir / f"psp_{p:03d}.png").read_bytes()
        en_raw = page(p, raw)
        (out_dir / f"psp_{p:03d}.png").write_bytes(en_raw)
        orig = Image.open(io.BytesIO(raw)).convert("RGB")
        en = Image.open(io.BytesIO(en_raw)).convert("RGB")
        cmp_im = Image.new("RGB", (orig.width, orig.height * 2), WHITE)
        cmp_im.paste(orig, (0, 0))
        cmp_im.paste(en, (0, orig.height))
        cmp_im.save(out_dir / f"cmp_{p:03d}.png")
    print(f"rendered {len(wanted)} manual pages -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
