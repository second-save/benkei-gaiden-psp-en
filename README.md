# Benkei Gaiden (PSN PC Engine Archives, NPJJ30035): English patch

An English patch for the PSN "PC Engine Archives" release of *Benkei Gaiden* (Sunsoft, 1989), the PSP
re-release of the PC Engine HuCard RPG.

The game itself is our English HuCard translation
([benkei-gaiden-pce-en](https://github.com/second-save/benkei-gaiden-pce-en), v1.0), placed inside the PSN
container. This patch also translates what only the PSN release has: the emulator's prompts and menus, the
18-page digital manual, the copyright notice screen, and the XMB title, picture and icons.

The patch holds no game data: you need your own copy of the game.

## Status: emulator release

- **Made for PPSSPP.** Tested in PPSSPP 1.20.4 on macOS.
- **Real PSP / PS Vita: untested.** The ISO's program (EBOOT) is signed again after patching, as the original
  was, but the patch applies to `CONTENT.DAT` in its decrypted form (the form PPSSPP reads).
- **No PSN flash reduction.** The PSN release's game ROM carries Sunsoft's 2010 changes that dim some screen
  flashes. The English game is built from the original HuCard, so the flashes are those of the 1989 game.
  Read the health warning (manual page 2) before you play.
- **Seen on screen:** the notice screen, every first-run prompt, the save dialog, the System Menu (L) and all
  18 manual pages. Rare prompts were translated but not seen: import/export, Memory Stick full, no Memory Stick.
- **Still in Japanese:** the CERO rating mark and the logos.

Please report problems in this repository's issues, with a screenshot and where you were in the game.

## Apply the patch

Two patches, one for each file. Each needs an unmodified dump:

| File | Original SHA-1 | Patched SHA-1 | Patch |
|---|---|---|---|
| `NPJJ30035/CONTENT.DAT` (decrypted, as PPSSPP reads it) | `cafecbc9345e3e1ecd73cebc08eea07d5be36f31` | `526d806730f8a497ddefe7720d62f3e694c50a81` | `benkei-gaiden-psn-en.xdelta` |
| the ISO (`Benkei Gaiden (Japan) (PCE) (PSN) [NPJJ30035].iso`) | `a5348957720e040c6cfdf68782fbd75662fa1db9` | `75c3b9600f173af1de79d1438a4e8e30b19f5d29` | `benkei-gaiden-psn-en-iso.xdelta` |

    xdelta3 -d -s CONTENT.DAT benkei-gaiden-psn-en.xdelta CONTENT.en.DAT
    xdelta3 -d -s "Benkei Gaiden (Japan) (PCE) (PSN) [NPJJ30035].iso" benkei-gaiden-psn-en-iso.xdelta "Benkei Gaiden (English).iso"

GUI patchers that take xdelta (such as Delta Patcher) work too. Then:

1. Rename `CONTENT.en.DAT` to `CONTENT.DAT`.
2. Put it in `PSP/GAME/NPJJ30035/` in PPSSPP's memory stick folder, in place of the original. Keep a copy of
   both originals.
3. In PPSSPP, start the English ISO.

The `CONTENT.DAT` patch alone also works with the original ISO: the game is in English and the emulator
prompts stay in Japanese.

## What changes

- **The game is in English**: the full script, menus, item, jutsu and enemy names, and the title and
  in-game graphics, from the HuCard translation (no honorifics, standard Hepburn, terms in `glossary.md`).
- **The emulator's prompts and menus** (`script/eboot.csv`, 71 strings): notices, autosave, Backup RAM,
  save and load, screen size, the System Menu and the manual viewer.
- **The manual**: all 18 pages redrawn in English (`tools/manual.py`), with the game's own names and terms.
- **The notice screen, XMB title, PIC0 and the game and save icons.**

## Build from source

You need python 3 with Pillow, a C compiler (for `sign_np`), xdelta3, the base dumps in `rom/` (`rom.sha1`) and
a built `../benkei-gaiden-pce/build/benkei_en.pce` (v1.0). Then:

    python3 -X utf8 tools/check.py           # dump hashes + tests
    python3.14 -X utf8 tools/build.py        # build/NPJJ30035/CONTENT.DAT + build/benkei_psp_en.iso
    tools/release.sh                         # dist/ patches + zip, each re-applied and compared

## Credits & Licence

- **Translation, engineering and AI assistance:** `second-save`.
- **Manual and notice font:** M+ 1p, SIL Open Font License (`fonts/OFL.txt`).
- **EBOOT signing:** sign_np by Hykem.
- *Benkei Gaiden* © 1989 Sunsoft. PC Engine Archives © 2010 Hudson Soft. This is an unofficial, non-commercial
  fan translation, not affiliated with the rights holders.
- Tools and English text: MIT Licence (`LICENSE`). Do not distribute the game files.
