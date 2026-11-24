"""CONTENT.DAT <-> plain VPCE archive for NPJJ30035.

The file is XORed with a 512-byte key repeating from offset 0. Scanning all 512-byte
blocks across the file recovers the key from 0xFF padding (present in GIMs), verified
against the VPCE archive magic (12 34 56 78).
"""
import collections
import sys

PERIOD = 512
MAGIC = b"\x12\x34\x56\x78"


def find_key(d: bytes) -> bytes:
    units = collections.Counter(d[i : i + PERIOD] for i in range(0, len(d) - PERIOD, PERIOD))
    for unit, _ in units.most_common(10):
        key = bytes(b ^ 0xFF for b in unit)
        if xor(d[:4], key[:4]) == MAGIC:
            return key
    raise AssertionError("could not recover 512-byte CONTENT.DAT XOR key")


def xor(d: bytes, key: bytes) -> bytes:
    k = int.from_bytes((key * (len(d) // PERIOD + 1))[: len(d)], "little")
    out = bytearray()
    step = 1 << 22
    if len(d) <= step:
        return (int.from_bytes(d, "little") ^ k).to_bytes(len(d), "little")
    for o in range(0, len(d), step):
        chunk = d[o : o + step]
        ck = (key * (len(chunk) // PERIOD + 1))[: len(chunk)]
        v = int.from_bytes(chunk, "little") ^ int.from_bytes(ck, "little")
        out += v.to_bytes(len(chunk), "little")
    return bytes(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    d = open(a[0], "rb").read()
    key = open(a[a.index("--key") + 1], "rb").read() if "--key" in a else find_key(d)
    assert len(key) == PERIOD
    if "--save-key" in a:
        open(a[a.index("--save-key") + 1], "wb").write(key)
    out = xor(d, key)
    open(a[1], "wb").write(out)
    print(f"wrote {a[1]} ({len(out)} bytes)")
