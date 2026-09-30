import struct, sys, os

def find_atoms(f, start, end, targets, depth=0, res=None):
    if res is None: res = []
    p = start
    while p < end - 8:
        f.seek(p)
        hdr = f.read(8)
        if len(hdr) < 8: break
        s = struct.unpack(">I", hdr[:4])[0]
        t = hdr[4:8].decode("ascii", "replace")
        hs = 8
        if s == 1:
            s = struct.unpack(">Q", f.read(8))[0]; hs = 16
        elif s == 0:
            s = end - p
        if s <= 0 or p + s > end: 
            break
        if t in targets:
            res.append((t, p, s, hs))
        if t in ("moov","trak","mdia","minf","stbl"):
            find_atoms(f, p+hs, p+s, targets, depth+1, res)
        p += s
    return res

def parse(path):
    sz = os.path.getsize(path)
    with open(path, "rb") as f:
        pos = 0; atoms = []
        while pos < sz - 8:
            f.seek(pos); hdr = f.read(8)
            if len(hdr) < 8: break
            size = struct.unpack(">I", hdr[:4])[0]
            typ = hdr[4:8].decode("ascii", "replace")
            hsize = 8
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]; hsize = 16
            elif size == 0:
                size = sz - pos
            atoms.append((typ, pos, size)); pos += size

        print(f"=== {os.path.basename(path)}  ({sz:,} B)  顶层: {[a[0] for a in atoms]}")
        moov = [a for a in atoms if a[0] == "moov"]
        if not moov:
            print("  !! 没有 moov —— 未封装完成"); return
        moov = moov[0]
        mdat = [a for a in atoms if a[0] == "mdat"][0]
        mdat_start, mdat_end = mdat[1] + 8, mdat[1] + mdat[2]

        # 每个 trak 单独校验
        traks = find_atoms(f, moov[1]+8, moov[1]+moov[2], {"trak"})
        for ti, (t, tp, ts_, ths) in enumerate(traks):
            stbl = find_atoms(f, tp+8, tp+ts_, {"stbl"})
            if not stbl: continue
            sp, ss = stbl[0][1], stbl[0][2]
            hdlr = find_atoms(f, tp+8, tp+ts_, {"hdlr"})
            htype = "?"
            f.seek(hdlr[0][1]+16); htype = f.read(4).decode("ascii","replace").strip()

            # stsz
            stsz = find_atoms(f, sp+8, sp+ss, {"stsz"})[0]
            f.seek(stsz[1]+8); f.read(4)
            sample_size, sample_count = struct.unpack(">II", f.read(8))
            if sample_size == 0:
                f.seek(stsz[1]+8+12+(sample_count-1)*4)
                last_size = struct.unpack(">I", f.read(4))[0]
            else:
                last_size = sample_size
            # stco
            stco = find_atoms(f, sp+8, sp+ss, {"stco","co64"})[0]
            f.seek(stco[1]+8); f.read(4)
            nchunks = struct.unpack(">I", f.read(4))[0]
            if stco[0] == "stco":
                f.seek(stco[1]+8+8+(nchunks-1)*4); last_off = struct.unpack(">I", f.read(4))[0]
            else:
                f.seek(stco[1]+8+8+(nchunks-1)*8); last_off = struct.unpack(">Q", f.read(8))[0]
            end_of_data = last_off + last_size
            pct = end_of_data / mdat_end * 100
            ok = mdat_start <= end_of_data <= mdat_end + 1
            print(f"  trak[{ti}] {htype}: samples={sample_count:,} chunks={nchunks:,} "
                  f"末样本结束={end_of_data:,} / mdat末={mdat_end:,} ({pct:.2f}%) {'OK 完整' if ok else '!! 异常 !!'}")

for p in sys.argv[1:]:
    parse(p); print()
