# Benkei Gaiden (PSP PC Engine Archives, NPJJ30035) — English translation

Skill: translate-retro-game (`~/.agents/skills/translate-retro-game/SKILL.md`; `python3 -X utf8 tools/skill.py`).
Hooks setup on fresh clone: `git config core.hooksPath tools/hooks`.

## Commands (run from repo root)
- Check: `python3 -X utf8 tools/check.py` (pre-commit hook runs this)
- Build: `python3.14 -X utf8 tools/build.py` (`--identity` for the roundtrip) -> `build/NPJJ30035/` + `build/benkei_psp_en.iso`
- Release: `tools/release.sh` -> `dist/` xdelta patches + zip (README must list both patched sha1)
- Build `sign_np`: `bash tools/build_sign_np.sh` -> `work/src/sign_np/sign_np`
- Headless QA: `tools/play.sh new SESSION [orig]` / `tools/play.sh SESSION keys...` (uses `PPSSPPHeadless`)
- Stock GUI boot: `python3 -X utf8 tools/pp.py start [orig]` / `python3.14 -X utf8 tools/pp.py fb OUT.png` / `python3 -X utf8 tools/pp.py stop`

## Paths
- Base dumps (`rom/`, gitignored; `rom.sha1`): `Benkei Gaiden (Japan) (PCE) (PSN) [NPJJ30035].iso` + `NPJJ30035/{CONTENT.DAT,PARAM.PBP,PSP-KEY.EDAT}`.
- Emulator: `tools/ppsspp/PPSSPPSDL.app/Contents/MacOS/PPSSPPSDL` (`HOME=work/pphome`, WebSocket port `43135`; Circle confirms).
- Sibling PCE translation: `../benkei-gaiden-pce/`.
- Docs: `docs/decisions.md`, `docs/fonts.md`, `glossary.md`, `docs/re/README.md`.

## Rules
- Edit source/data files only with the file-edit tool; never shell heredocs or `sed -i`.
- Use `python3 -X utf8` for stdlib scripts; `python3.14 -X utf8` when Pillow/numpy/capstone are needed.
- Everything patched ships inside the ISO (`~PSP`-signed `EBOOT.BIN`, `PARAM.SFO`, `CONFIG.PSP`, `PIC0.PNG`) and rebuilt `NPJJ30035/CONTENT.DAT` (no `PSP/TEXTURES/`, no plain ELF `EBOOT.BIN`).

## Status
`docs/status.md`: done, next, open items. Update at every phase end.
