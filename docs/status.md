# Status — Benkei Gaiden (PSP PC Engine Archives, NPJJ30035)

## Current Phase
- **Phase 0 & Phase 1 (Setup, Identity Gate & Recon):** Complete — ready for Phase 2+ implementation planning (build pipeline, EBOOT/XMB/GIM/manual translation, headless QA, and xdelta3 release).

## Done
- **Phase 0:** Initialized `benkei-gaiden-psp` on `main` (`second-save`, `core.hooksPath tools/hooks`), pinned clean ISO + `NPJJ30035/{CONTENT.DAT,PARAM.PBP,PSP-KEY.EDAT}` in `rom.sha1`, fetched stock `PPSSPP` v1.20.4 (`tools/pp.py`, port `43135`), added `tools/play.sh` (`PPSSPPHeadless`), and built `work/src/sign_np/sign_np`.
- **Phase 3 (Identity Gate):** Implemented `tools/content_xor.py` and `tools/vpce.py`; `tests/test_identity.py` passes byte-identical roundtrips for both `CONTENT.DAT` (preserving 28-byte EOF tail) and the PSP UMD ISO (`iso9660.patch`).
- **Phase 1 (Recon & Empirical Verification):**
  - Dumped `work/eboot_jp.elf` (`708,656` B, `SHA-1: 1b8c2e90c1243c0a2480b22ba1322592572f4abf`), verified `sign_np` tag-2 (`0xD9160BF0`) re-signing, matched `71/71` `psnvpce` UTF-8 strings (`0x817A0..0x82CB8`), and confirmed no extra JP UTF-8 strings via `jpscan.py`.
  - Diffed `N43302SL.PCE` vs No-Intro `.pce` (only 9 banks carry 2010 `$E6`/`$E7` flash-dampening counters; no `psnvpce` hooks).
  - Empirically verified `1 MiB` `benkei_en.pce` inside `NPJJ30035/CONTENT.DAT` (`xdelta3` = `109,595` B) in `PPSSPPHeadless`: boots splash/title, executes `$61..$7E` far-bank dialogue in Rinsho-ji, opens `Continue -> Save RAM -> Benkei 1..3`, and displays `L` System Menu & `001/018` manual.
  - Completed full GIM roundtrip check (`chyuikanki_PSP.GIM`, `HUDSON.GIM` == Ziria, `WALL.GIM` == Ziria) and surveyed all 18 `480×248` manual pages + XMB images (`docs/re/graphics_survey.md`).

## Next
- Hand back for Phase 2–9 PSP execution plan (`script/eboot.csv` ported to `0x817A0..0x82CB8`, XMB/CONFIG/PARAM.SFO/GIM localization, 18-page manual typesetting + EN screenshots, PPSSPPHeadless QA routes + saves, and xdelta3 release packager).
