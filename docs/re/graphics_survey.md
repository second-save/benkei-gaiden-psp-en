# Graphics, XMB, and Digital Manual Survey (`NPJJ30035`)

Every visual asset in the ISO and `CONTENT.DAT` has been unpacked, decoded/checked, and visually surveyed.

---

## 1. ISO XMB & Container GIM Assets

| Asset | Location | Dimensions / Format | SHA-1 (unpacked) | Matches `NPJJ30029` | Translation Scope (`D4`/`D6`) |
|---|---|---|---|---|---|
| `PARAM.SFO` (`TITLE`) | ISO `/PSP_GAME/` | UTF-8 string (`128` B slot) | `25678ff3df40178c...` | No (`弁慶外伝`) | `Benkei Gaiden` (already `SYS_TITLE_US="BENKEI GAIDEN"` in `CONFIG.PSP`) |
| `CONFIG.PSP` (`SYS_TITLE_JP`) | ISO `/PSP_GAME/USRDIR/` | UTF-8 text (`4,115` B) | `f2dc3ca48da312bb...` | Game-specific | Update `SYS_TITLE_JP="Benkei Gaiden"` so PSP Save Utility displays English title |
| `PIC0.PNG` | ISO `/PSP_GAME/` | `310×180` RGBA PNG | `e988a6c6cdc4d143...` | Game-specific | Translate `弁慶外伝` -> `Benkei Gaiden` & 3-line PSN notice; keep rounded alpha, `PC Engine` circle, `PS3`/`PSP` pills (`CERO A` either kept or adapted) |
| `ICON0.PNG` & `SAVEDATA.PNG` | ISO & `CONTENT.DAT` | `80×80` RGB PNG (identical) | `0d9993df02f1b247...` | Game-specific | Replace vertical red JP calligraphy `弁慶 ―外伝―` with localized `BENKEI GAIDEN` logo over the shrine art; keep left HuCARD grip + `PC Engine` emblem |
| `chyuikanki_PSP.GIM` | `CONTENT.DAT` | `480×272` `rgba8888` (`swz=1`) | `fcf984c6eb302452...` | Not in Ziria | Full-screen 2010 Copyright Act warning (`ご注意`). `gim.py` roundtrip lossless (`raw_eq=True`, `pixel_diff=None`). Translate all text into English; keep warning triangle icon |
| `HUDSON.GIM` | `CONTENT.DAT` | `480×272` `rgba8888` (`swz=1`) | `bfdd8c4bf65133a4...` | **Yes** | Already English (`HUDSON®` bee logo). Keep untouched |
| `WALL.GIM` | `CONTENT.DAT` | `408×204` `rgba5551` (`swz=1`) | `981f6ee0f00ec3f5...` | **Yes** | Patterned `PC Engine` side wallpaper with no Japanese text. Keep untouched |

---

## 2. Digital Manual (`psp_001.png` .. `psp_018.png` in `CONTENT.DAT`)

All 18 manual pages are **`480×248` RGB PNGs** displayed above the `24` px `psnvpce` viewer footer (`248 + 24 = 272` px PSP screen).

| Page | Title (JP -> EN) | Category | Screenshots / Icons | Notes for English Redraw (`tools/manual.py`) |
|---|---|---|---|---|
| `psp_001.png` | Cover: `弁慶外伝` -> `Benkei Gaiden` | Benkei cover + boilerplate | Left HuCARD sidebar title screen (JP) + `PC Engine` / `PS3` / `PSP` badges | Translate tagline (`Kijaku`), table (`Role-Playing`, `1 Player`, `PC Engine (HuCARD)`, `SUNSOFT`, `Dec 1989`), `PC Engine Archives`, `Manual`, and swap in EN title art |
| `psp_002.png` | `健康のためのご注意` -> `Health Precautions` | Generic PSP (`== Ziria`) | Two `⚠` warning triangles, bullets | Translate generic photosensitive seizure & play-break precautions |
| `psp_003.png` | `使用上のご注意` -> `Precautions for Use` | Generic PSP (`== Ziria`) | EN trademark footer with logos | Translate 2 Japanese bullets (`For PSP® use only`, keep firmware updated); preserve bottom EN trademark block |
| `psp_004.png` | `PSP®でのプレイに関して①` -> `Playing on PSP® (1)` | Generic `psnvpce` | `[L]` button icon | Use exact `glossary.md` / `EBOOT.BIN` menu names: `Manual`, `Save (Suspend)`, `Load (Resume)`, `Screen Size`, `Backup RAM Data`, `Autosave` |
| `psp_005.png` | `PSP®でのプレイに関して②` -> `Playing on PSP® (2)` | Generic `psnvpce` | `[△] [○] [□] [×]` icons | Soft reset (`START + SELECT`) warning & rapid-fire turbo table |
| `psp_006.png` | `ゲーム内のボタン表記に関して` -> `In-Game Button Names` | Generic `psnvpce` | PSP line diagram, `[○] [×]` | Map `START->RUN`, `SELECT->SELECT`, `○->I`, `×->II` (`In-Game Name`) |
| `psp_007.png` | `セーブについて（中断セーブ）` -> `Saving (Suspend Save)` | Generic `psnvpce` | Cropped PSP XMB screenshot (JP) | Use `Memory Stick™`, `Saved Data Utility`, `Backup RAM Data`; relabel XMB inset in English (`Game` / `Saved Data Utility`) |
| `psp_008.png` | `操作方法` -> `Controls` | **Benkei-specific** | PSP hardware photo, button icons | `Move / Select Command`, `Reorder Party` (`SELECT`), `Start` (`START`), `Confirm / Open Command Window` (`○`), `Cancel / View Status` (`×`) |
| `psp_009.png` | `ゲームのはじめかた` -> `Starting the Game` | **Benkei-specific** | Title screen (JP `冒頭`/`継続`) | Reference `New Game`, `Continue`, `Password`, `Save RAM`; swap in EN title screen capture |
| `psp_010.png` | `ゲームの進めかた` -> `How to Play` | **Benkei-specific** | Clean overworld screenshot (no JP text) | Translate 3 story/gameplay paragraphs (`Hogen`, `Kijaku`, `Rinsho-ji`, `Tsukumo Village`, `Demon Realm`, `Revive`); keep map shot |
| `psp_011.png` | `画面の見かた` -> `Screen Layout` | **Benkei-specific** | Status & Battle screenshots (heavy JP) | Translate legend ①–⑪ and replace both insets with EN Status & Battle captures matching ①–⑪ markers |
| `psp_012.png` | `コマンドについて` -> `Commands` | **Benkei-specific** | Tables only | Use exact `b02_sys.json` names: Field (`Talk`, `Stats`, `Equip`, `Jutsu`, `Items`, `Check`) & Battle (`Fight`, `Jutsu`, `Flee`, `Items` / `Item`) |
| `psp_013.png` | `法術について①` -> `Jutsu (1)` | **Benkei-specific** | `鬼` / `沙` user badges | 8 attack jutsu (`b0e_jutsu.json`: `Soul Break`..`Goku-Muten`) + localized `Ki`/`Sy` badges |
| `psp_014.png` | `法術について②` -> `Jutsu (2)` | **Benkei-specific** | `鬼` / `沙` user badges | 11 support/field jutsu (`Heal`, `Full Heal`, `Grand Heal`, `Revive`, `Purify`, `Raise Might`, `Halt Strike`, `Seal Jutsu`, `Smokescreen`, `Swift Step`, `Holy Step`) |
| `psp_015.png` | `装備品について` -> `Equipment` | **Benkei-specific** | `鬼` / `三` / `沙` / `弁` equip badges | 21 items across Weapons / Armor / Accessories (`b0e_items.json`) + `Ki`/`Sb`/`Sy`/`Be` badges |
| `psp_016.png` | `道具について` -> `Items` | **Benkei-specific** | Table only | 8 consumable/key items (`Salve`, `Great Salve`, `Antidote`, `Realm Elixir`, `Ward Incense`, `Echo Mirror`, `Dream Lens`, `Calm Flute`) |
| `psp_017.png` | `バックアップRAMへのセーブ` -> `Saving to Backup RAM` | Hybrid (`psnvpce` + Benkei) | Shrine BRAM screenshot (JP) | Translate PS3/BRAM note + shrine `Password` / `Save RAM` guide; swap in EN shrine screenshot |
| `psp_018.png` | `この商品に関するお問い合わせ先` -> `Support & Credits` | Hudson colophon + SUNSOFT | `HUDSON®` bee, inline `PC Engine` | Translate support hours/disclaimer, NEC/Hudson/DynaFont notices; preserve `©1989-2010 SUNSOFT` & `HUDSON®` |
