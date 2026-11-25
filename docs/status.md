# Status — Benkei Gaiden (PSP PC Engine Archives, NPJJ30035)

## Current Phase
**Published 2026-11-25** (user's go): public repo `second-save/benkei-gaiden-psp-en`, release `v1.0` with
the zip and both xdelta patches. README media in `docs/media/` (session `work/play/en`, GIFs via `tools/gif.py`).

## Builds
- `python3.14 -X utf8 tools/build.py` -> `build/NPJJ30035/CONTENT.DAT` sha1 `526d806730f8a497ddefe7720d62f3e694c50a81`
  and `build/benkei_psp_en.iso` sha1 `75c3b9600f173af1de79d1438a4e8e30b19f5d29` (same output every run).
  `--identity` asserts CONTENT.DAT rebuilds byte-identical.
- `tools/release.sh` -> `dist/benkei-gaiden-psn-en{,-iso}.xdelta` (717 KB / 751 KB) + `dist/benkei-gaiden-psn-en.zip`
  (both patches + README), each re-applied and compared.

## What the build replaces
- CONTENT.DAT: `N43302SL.PCE` = `../benkei-gaiden-pce/build/benkei_en.pce` (pinned sha1 `9e6ffc62…`, PCE v1.0),
  `psp_001..018.png` (`tools/manual.py`), `chyuikanki_PSP.GIM` notice and `SAVEDATA.PNG` (`tools/gfx_psp.py`).
- ISO (`tools/frontend.py`): EBOOT strings from `script/eboot.csv` (71), re-signed with sign_np tag 2;
  PARAM.SFO + CONFIG.PSP title "Benkei Gaiden"; PIC0 and ICON0.
- D10: the PSN ROM's 2010 flash-reduction changes are not carried over (README caveat).

## QA (PPSSPPHeadless, session `work/play/en`, cold boot of the build)
Seen in English: notice GIM, start notice, autosave notice, Backup RAM create/created, screen-size menu and hint,
"no save data" prompt, save dialog (icon, "Save Data"), Sunsoft logo, English title, prologue crawl, System Menu,
manual viewer pages 1–18 (`work/qa/manual/viewer.png`). Not seen: import/export, Memory-Stick-full and
no-Memory-Stick prompts.

## Next
- Player reports via GitHub issues; optional: port the PSN flash reduction (D10).
