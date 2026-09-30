import struct, sys, os

def walk(f, start, end, depth=0, out=None):
    pos = start
    while pos < end - 8:
        f.seek(pos)
        hdr = f.read(8)
        if len(hdr) < 8:
            break
        size = struct.unpack(">I", hdr[:4])[0]
        typ = hdr[4:8]
        try:
            t = typ.decode("ascii")
        except Exception:
            t = repr(typ)
        if not t.isprintable() or len(t) != 4:
            out.append("  " * depth + f"[?] 非标准 atom @ {pos}: {hdr!r}")
            break
        hsize = 8
        if size == 1:
            size = struct.unpack(">Q", f.read(8))[0]
            hsize = 16
        elif size == 0:
            size = end - pos
        out.append("  " * depth + f"{t:8s} size={size:>14,}  @ {pos:,}  -> {pos+size:,}")
        if t in ("moov", "trak", "mdia", "minf", "stbl", "udta", "mvex"):
            walk(f, pos + hsize, pos + size, depth + 1, out)
        pos += size

def probe(path):
    sz = os.path.getsize(path)
    out = []
    out.append(f"=== {path}")
    out.append(f"    文件大小: {sz:,} 字节 ({sz/1024/1024/1024:.3f} GB)")
    with open(path, "rb") as f:
        walk(f, 0, sz, 0, out)
    return "\n".join(out)

for p in sys.argv[1:]:
    print(probe(p))
    print()
