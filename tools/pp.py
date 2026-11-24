"""Drive stock PPSSPPSDL on macOS for NPJJ30035 (isolated HOME in work/pphome, WebSocket port 43135).

    pp.py start [orig|DIR] [--save DIR] [--dump-eboot]
    pp.py fb OUT.png            capture framebuffer (480x272) via debugger memory.read
    pp.py shot OUT.png          capture via gpu.buffer.screenshot
    pp.py stop                  kill running PPSSPPSDL process
    pp.py keys "BTN+BTN" FRAMES hold buttons for FRAMES (60 Hz wall clock), then release
    pp.py mem ADDR SIZE OUT     dump PSP memory range to file
"""
import base64
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill import SKILL  # noqa: E402

sys.path.insert(0, os.path.join(SKILL, "scripts"))
import psp  # noqa: E402

TITLE_ID = "NPJJ30035"
PORT = 43135
HOME = os.path.join(ROOT, "work", "pphome")
SYS = os.path.join(HOME, ".config", "ppsspp", "PSP", "SYSTEM")
PID = os.path.join(ROOT, "work", "pp.pid")
EXE = os.path.join(ROOT, "tools", "ppsspp", "PPSSPPSDL.app", "Contents", "MacOS", "PPSSPPSDL")


def set_ini(dump_eboot: bool = False) -> None:
    os.makedirs(SYS, exist_ok=True)
    p = os.path.join(SYS, "ppsspp.ini")
    txt = open(p, encoding="utf-8-sig").read() if os.path.exists(p) else "[General]\n[Sound]\n[Graphics]\n"
    ini = {
        "RemoteDebuggerOnStartup": "True",
        "RemoteISOPort": str(PORT),
        "Enable": "False",
        "GlobalVolume": "0",
        "FirstRun": "False",
        "FullScreen": "False",
        "SoftwareRenderer": "True",
        "DumpFileTypes": "7" if dump_eboot else "0",
    }
    for k, v in ini.items():
        txt, n = re.subn(r"(?m)^%s = .*$" % k, f"{k} = {v}", txt)
        if not n:
            sec = "[Sound]" if k in ("Enable", "GlobalVolume") else "[Graphics]" if k in ("FullScreen", "SoftwareRenderer") else "[General]"
            txt = txt.replace(sec, f"{sec}\n{k} = {v}", 1)
    open(p, "w", encoding="utf-8").write(txt)


def ws():
    return psp.WS(PORT, timeout=60)


def main() -> None:
    cmd, a = sys.argv[1], sys.argv[2:]
    if cmd == "start":
        dump_eboot = "--dump-eboot" in a
        pos = [x for x in a if not x.startswith("--") and not (a.index(x) > 0 and a[a.index(x) - 1] == "--save")]
        target = pos[0] if pos else ""
        en_iso = os.path.join(ROOT, "build", "benkei_psp_en.iso")
        if target and os.path.isfile(target):
            iso = target
        elif target != "orig" and os.path.exists(en_iso):
            iso = en_iso
        else:
            iso = glob.glob(os.path.join(ROOT, "rom", "*.iso"))[0]

        if target and os.path.isdir(target):
            src = target
        elif target == "orig" or not os.path.exists(os.path.join(ROOT, "build", TITLE_ID)):
            src = os.path.join(ROOT, "rom", TITLE_ID)
        else:
            src = os.path.join(ROOT, "build", TITLE_ID)

        dst = os.path.join(HOME, ".config", "ppsspp", "PSP", "GAME", TITLE_ID)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)

        if "--save" in a:
            sv = a[a.index("--save") + 1]
            sd = os.path.join(HOME, ".config", "ppsspp", "PSP", "SAVEDATA")
            for d in glob.glob(os.path.join(sd, f"{TITLE_ID}*")):
                shutil.rmtree(d)
            if sv != "none":
                shutil.copytree(sv, sd, dirs_exist_ok=True)

        set_ini(dump_eboot=dump_eboot)
        os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
        log = open(os.path.join(ROOT, "work", "pp.log"), "w")
        p = subprocess.Popen(
            [EXE, os.path.abspath(iso)],
            stdout=log,
            stderr=log,
            env=dict(os.environ, HOME=HOME),
            start_new_session=True,
        )
        open(PID, "w").write(str(p.pid))
        print("pid", p.pid, "iso", os.path.basename(iso), "content", src)
    elif cmd == "stop":
        try:
            os.kill(int(open(PID).read()), signal.SIGKILL)
        except (OSError, ValueError) as e:
            print("not running:", e)
        set_ini(dump_eboot=False)
    elif cmd == "shot":
        w = ws()
        if not w.call("cpu.status")["stepping"]:
            w._send(1, json.dumps({"event": "cpu.stepping"}).encode())
            w.wait("cpu.stepping")
        r = w.call("gpu.buffer.screenshot")
        open(a[0], "wb").write(base64.b64decode(r["uri"].split(",")[1]))
        w.call("cpu.resume")
    elif cmd == "fb":
        from PIL import Image

        d = ws().mem(0x04000000, 512 * 272 * 2)
        im = Image.frombuffer("RGB", (512, 272), d, "raw", "BGR;16", 0, 1)
        b, g, r = im.split()
        Image.merge("RGB", (r, g, b)).crop((0, 0, 480, 272)).save(a[0])
    elif cmd == "call":
        kw = {}
        for x in a[1:]:
            k, v = x.split("=", 1)
            try:
                kw[k] = json.loads(v)
            except ValueError:
                kw[k] = v
        print(json.dumps(ws().call(a[0], **kw), indent=1)[:6000])
    elif cmd == "mem":
        w = ws()
        addr, size = int(a[0], 16), int(a[1], 16)
        with open(a[2], "wb") as f:
            for o in range(0, size, 1 << 20):
                f.write(w.mem(addr + o, min(1 << 20, size - o)))
    elif cmd == "keys":
        w = ws()
        keys = set() if a[0] == "-" else set(a[0].split("+"))
        w.call("input.buttons.send", buttons={k: (k in keys) for k in psp.BUTTONS})
        time.sleep(int(a[1]) / 60)
        w.call("input.buttons.send", buttons={k: False for k in psp.BUTTONS})


if __name__ == "__main__":
    main()
