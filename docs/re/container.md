# Container & Executable Analysis (`NPJJ30035` — Virtual PC Engine for PSP Network)

`NPJJ30035` is Sony/Hudson's PSN **PC Engine Archives** release of *Benkei Gaiden* (*弁慶外伝*). It pairs a PSP ISO frontend running Sony/Hudson's PC Engine emulator (`psnvpce`) with `ms0:/PSP/GAME/NPJJ30035/CONTENT.DAT` on the Memory Stick.

---

## 1. PSP UMD ISO (`Benkei Gaiden (Japan) (PCE) (PSN) [NPJJ30035].iso`)

- **Size:** `111,050,752` B (`SHA-1: a5348957720e040c6cfdf68782fbd75662fa1db9`)
- **Identity check:** `iso9660.patch(ISO, out, {"/PSP_GAME/PARAM.SFO": orig_sfo})` reproduces the base ISO byte-for-byte (`tests/test_identity.py`).
- **Key files (`iso9660.py list`):**
  - `/PSP_GAME/PARAM.SFO` (`728` B): `DISC_ID=NPJJ30035`, `TITLE='弁慶外伝'` (`128`-byte UTF-8 slot at `0x254`), `DISC_VERSION='1.02'`, `PSP_SYSTEM_VER='6.20'`.
  - `/PSP_GAME/SYSDIR/EBOOT.BIN` (`708,656` B, `SHA-1: ed6985e2f46669ffa7d75f53910e30e18fd28f2f`): encrypted `~PSP` executable (`tag 2 = 0xD9160BF0` at `+0xD0`).
    - Decrypted dump (`DumpFileTypes = 7`): `708,656` B ELF (`SHA-1: 1b8c2e90c1243c0a2480b22ba1322592572f4abf`).
    - Re-signing with `sign_np -elf work/eboot_jp.elf ... 2` yields a `708,992` B `~PSP` file with `f00b16d9` at `+0xD0`.
    - **UI string table (`0x817A0..0x82CB8`):** 4-byte-aligned NUL-terminated UTF-8 strings (`\r\n` line breaks). All **71/71** `psnvpce` UI prompts/System Menu entries from sibling `tengai-makyou-ziria-psp` (`NPJJ30029`) match cleanly at `-0x7DC8` offset shift. `jpscan.py` confirms no additional Japanese UTF-8 strings exist in the binary.
  - `/PSP_GAME/USRDIR/CONFIG.PSP` (`4,115` B, UTF-8): defines `TITLE_ID="NPJJ30035"`, `SYS_TITLE_JP="弁慶外伝"`, `SYS_TITLE_US="BENKEI GAIDEN"`, `ROM_NAME="N43302SL.PCE"`, `MAN_PREFIX="psp_"`, `MAN_PAGE_MAX=18`, `MAN_PAGE_WIDTH=480`, `MAN_PAGE_HEIGHT=960`.
  - `/PSP_GAME/ICON0.PNG` (`6,672` B, `80×80`), `/PSP_GAME/PIC0.PNG` (`43,781` B, `310×180`).
  - `/PSP_GAME/USRDIR/{LIBFONT.PRX,UCS2JIS.BIN,JIS2UCS.BIN}`, `BOOT.BIN`, `OPNSSMP.BIN`, `SYSDIR/UPDATE/*`: system modules/data left untouched.

---

## 2. Memory Stick Container (`NPJJ30035/CONTENT.DAT`)

- **Size:** `2,680,240` B (`SHA-1: cafecbc9345e3e1ecd73cebc08eea07d5be36f31`), plus `PARAM.PBP` (`51,221` B) and `PSP-KEY.EDAT` (`16` B).
- **Outer XOR layer (`tools/content_xor.py`):** 512-byte key repeating from offset `0`. Because the second half consists mainly of compressed/audio assets (`0xFF` blocks repeated only 2× there), `find_key()` scans the entire file (`0xFF` padding repeated 866× in `chyuikanki_PSP.GIM` / `HUDSON.GIM`) and verifies the `12 34 56 78` VPCE header magic (`key SHA-1: 86af983b17329c96359114c5647f69144dd4849b`). The final 28 bytes of raw `CONTENT.DAT` (`2,680,212..2,680,240`) are `0x00`; XOR-decoding maps them to trailing padding preserved by `vpce.pack()` for a byte-identical roundtrip (`tests/test_identity.py`).
- **Inner VPCE archive (`tools/vpce.py`, `25` entries):**
  - `chyuikanki_PSP.GIM` (`522,452` B), `CONFIG.PS3` (`3,519` B), `HUDSON.GIM` (`522,464` B)
  - `N43302SL.PCE` (`393,216` B, `SHA-1: 0be41c774e7ee75b84efdc2b05a7a45ec0201503`)
  - `psp_001.png` .. `psp_018.png` (`480×248` RGB PNG manual pages)
  - `SAVEDATA.PNG` (`6,672` B, byte-identical to `ICON0.PNG`), `SNDBANK0.PSM` (`437,600` B), `WALL.GIM` (`169,924` B)
- **Mod-512 alignment (`vpce.pack(..., mod512=True)`):** Keeping every unchanged entry after `N43302SL.PCE` at its original `offset % 512` preserves their XOR ciphertext unchanged. An `xdelta3 -B 2680240` patch from clean `CONTENT.DAT` to the 1 MiB expanded `benkei_en.pce` test container is **`109,595` B** (`107 KiB`).

---

## 3. `N43302SL.PCE` vs. No-Intro HuCard (`Benkei Gaiden (Japan).pce`)

Diffing all 48 banks (`393,216` B) shows **39 banks byte-identical** (including `b11_dialogue`, `b0e`, `b0d`, and all `BG[]` / `SPR[]` graphics) and **9 code/layout banks modified** (`B$00`: 7,081 B, `B$01`: 3,122 B, `B$02`: 6,491 B, `B$08`: 489 B, `B$09`: 606 B, `B$0A`: 12 B, `B$1B`: 3,194 B, `B$1C`: 179 B, `B$1F`: 196 B).
Disassembly (`dishuc.py`) confirms these changes are Hudson/Sunsoft's 2010 PSN/VC photosensitive-flash safety patches:
- Zero-page counters `$E6` and `$E7` throttle screen flash routines in NMI (`B$00:$EAC9` / `EB40`), prologue/fade loops (`B$02:$C719` / `C87D`), and 4-hero battle hit flashes (`B$1B:$73C5`..`7408`).
- No `psnvpce`-specific trap or emulator hook exists in `N43302SL.PCE`. Because those flash patches occupy tail bytes near `B$00:$FF8E` and `B$02:$DFDA`, substituting our expanded `1 MiB` `benkei_en.pce` directly requires zero assembly relocation.

---

## 4. Empirical Verification of `1 MiB` HuCard & Backup RAM in `PPSSPPHeadless`

Tested `work/test_1m/NPJJ30035/CONTENT.DAT` (`N43302SL.PCE` replaced with `../benkei-gaiden-pce/build/benkei_en.pce`, `1,048,576` B) using frame-deterministic `PPSSPPHeadless` (`--ppge`):
- **First-run flow:** Accepts legal notice (`chyuikanki_PSP.GIM`), Autosave notice, creates `SAVEDATA/NPJJ30035` (`Backup RAM`) & `NPJJ30035GAME1` (`Save Data`), selects `Screen Size` (`cross`), and enters the PCE runtime on `circle` after `"Load/Save completed."`.
- **Title & Splash:** `SUNSOFT(R)` + `DREAMS - CREATION - SUNSOFT` and crimson brush `BENKEI GAIDEN` logo + `New Game / Continue` menu render cleanly (`work/qa/h_boot2`, `h_title`).
- **Expanded Bank Reads (`$61..$7E`):** Selecting `New Game` (`circle` = PCE `I`) advances into Rinsho-ji Temple and renders `Yoichi: "Demons stormed the village! They've taken O-Koto!"` cleanly (`work/qa/h_dialogue/f001650.png`).
- **Backup RAM:** Selecting `Continue` -> `Save RAM` opens `Load which one? Benkei 1 / Benkei 2 / Benkei 3 / Cancel` cleanly (`work/qa/h_bram7/f000670.png`).
- **PSP System Menu & Manual Viewer (`L`):** Opens System Menu and displays `psp_001.png` (`001/018`) cleanly at `480×248` above the emulator footer bar (`work/qa/h_dialogue/final.png`).
