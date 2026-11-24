# Reverse-Engineering Notes Index (`NPJJ30035`)

- [`container.md`](container.md): ISO9660 layout, `EBOOT.BIN` (`eboot_jp.elf` & 71-string table at `0x817A0..0x82CB8`), `CONTENT.DAT` XOR key + VPCE archive, `N43302SL.PCE` flash-patch diff analysis, and `PPSSPPHeadless` `1 MiB` HuCard + BRAM verification.
- [`graphics_survey.md`](graphics_survey.md): Survey of ISO XMB graphics (`PIC0.PNG`, `ICON0.PNG`), `CONTENT.DAT` assets (`SAVEDATA.PNG`, `chyuikanki_PSP.GIM`, `HUDSON.GIM`, `WALL.GIM`), and all 18 `480×248` manual pages (`psp_001..018.png`).
