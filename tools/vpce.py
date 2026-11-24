"""Virtual PC Engine (PSN) CONTENT archive unpacker/packer.

Layout after content_xor: 0x80-byte header (magic 12 34 56 78, count u32 at 0x28),
0x50-byte entry descriptors (name[0x40], offset u32, size u32, 8 zero bytes), then
16-byte aligned payloads. Unchanged entries preserve their original padding bytes;
when replacing resized entries, files may optionally keep mod-512 alignment or re-pack
with 16-byte alignment (keeping the trailing 28-byte raw zero tail behavior documented).
"""
import os
import struct
import sys

HDR, ENT = 0x80, 0x50


def entries(d: bytes) -> list[tuple[str, int, int]]:
    assert d[:4] == b"\x12\x34\x56\x78", "not a plain VPCE archive (run content_xor first)"
    n = struct.unpack_from("<I", d, 0x28)[0]
    out = []
    for i in range(n):
        o = HDR + i * ENT
        name = d[o : o + 0x40].split(b"\0")[0].decode("ascii")
        off, size = struct.unpack_from("<II", d, o + 0x40)
        out.append((name, off, size))
    return out


def pack(d: bytes, repl: dict[str, bytes], mod512: bool = True) -> bytes:
    ents = entries(d)
    unknown = set(repl) - {n for n, _, _ in ents}
    assert not unknown, f"not in archive: {unknown}"
    out = bytearray(d[: HDR + len(ents) * ENT])
    order = sorted(range(len(ents)), key=lambda i: ents[i][1])
    pos = ents[order[0]][1]
    assert pos == len(out)
    for k, i in enumerate(order):
        name, off, size = ents[i]
        if mod512:
            out += b"\0" * ((off - pos) % 512)
            pos = len(out)
        else:
            pad0 = (-pos) % 16
            if pad0:
                out += b"\0" * pad0
                pos = len(out)
        end = ents[order[k + 1]][1] if k + 1 < len(order) else len(d)
        body = repl.get(name)
        if body is None:
            body, pad = d[off : off + size], d[off + size : end]
        else:
            pad = b"\0" * (-len(body) % 16)
        struct.pack_into("<II", out, HDR + i * ENT + 0x40, pos, len(body))
        out += body + pad
        pos = len(out)
    return bytes(out)


if __name__ == "__main__":
    cmd, arc = sys.argv[1], sys.argv[2]
    d = open(arc, "rb").read()
    if cmd == "list":
        for name, off, size in entries(d):
            print(f"{off:08X} {size:9d} {name}")
    elif cmd == "x":
        os.makedirs(sys.argv[3], exist_ok=True)
        for name, off, size in entries(d):
            open(os.path.join(sys.argv[3], name), "wb").write(d[off : off + size])
    elif cmd == "pack":
        repl = {}
        for a in sys.argv[4:]:
            n, p = a.split("=", 1)
            repl[n] = open(p, "rb").read()
        open(sys.argv[3], "wb").write(pack(d, repl))
