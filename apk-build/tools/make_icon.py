"""纯 Python 生成启动图标。

输出两套：
  ic_launcher.png            传统图标（圆角深底 + 图案），给 Android 8 以下用
  ic_launcher_foreground.png 自适应图标的前景层（透明底，图案收在安全区内），配合 anydpi-v26 的 xml
"""
import math
import os
import struct
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'res')


def write_png(path, w, h, buf):
    rows = b''.join(b'\x00' + bytes(buf[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(rows, 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def over(dst, src):
    sa = src[3]
    if sa <= 0:
        return dst
    da = dst[3]
    ra = sa + da * (1 - sa)
    if ra <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        (src[0] * sa + dst[0] * da * (1 - sa)) / ra,
        (src[1] * sa + dst[1] * da * (1 - sa)) / ra,
        (src[2] * sa + dst[2] * da * (1 - sa)) / ra,
        ra,
    )


def round_rect_alpha(x, y, r):
    cx = min(max(x, r), 1 - r)
    cy = min(max(y, r), 1 - r)
    dx = x - cx
    dy = y - cy
    return 1.0 if dx * dx + dy * dy <= r * r else 0.0


def content(x, y, scale=1.0):
    """图案层：青色进度环 + 番茄 + 高光 + 绿叶。不含背景。"""
    if scale != 1.0:
        x = (x - 0.5) / scale + 0.5
        y = (y - 0.52) / scale + 0.52

    col = (0.0, 0.0, 0.0, 0.0)

    # 青色进度环，缺口朝上
    dx = x - 0.5
    dy = y - 0.585
    d = math.hypot(dx, dy)
    ring_r, ring_w = 0.352, 0.030
    if abs(d - ring_r) <= ring_w * 0.5:
        a = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
        if 16 <= a <= 344:
            col = over(col, (0.133, 0.827, 0.933, 0.92))

    # 番茄本体（径向渐变）
    r = 0.248
    if d <= r:
        k = d / r
        rr = 1.000 - 0.230 * k * k
        gg = 0.420 - 0.250 * k * k
        bb = 0.290 - 0.190 * k * k
        col = over(col, (min(rr, 1), min(gg, 1), min(bb, 1), 1.0))

        # 左上高光
        hx = (x - 0.415) / 0.105
        hy = (y - 0.500) / 0.075
        hd = hx * hx + hy * hy
        if hd < 1.0:
            col = over(col, (1.0, 0.95, 0.92, 0.20 * (1 - hd)))

    # 蒂：短茎 + 三片叶
    sx, sy = 0.5, 0.352
    if -0.075 <= (y - sy) <= 0.012 and abs(x - sx) <= 0.016:
        col = over(col, (0.180, 0.400, 0.180, 1.0))
    for ox, oy, rx, ry, rot in ((-0.070, 0.006, 0.082, 0.034, 28),
                                (0.070, 0.006, 0.082, 0.034, -28),
                                (0.0, -0.004, 0.070, 0.030, 0)):
        lx = x - (sx + ox)
        ly = y - (sy + oy)
        rad = math.radians(rot)
        ux = (lx * math.cos(rad) + ly * math.sin(rad)) / rx
        uy = (-lx * math.sin(rad) + ly * math.cos(rad)) / ry
        e = ux * ux + uy * uy
        if e <= 1.0:
            col = over(col, (0.220 + 0.080 * (1 - e), 0.640 + 0.120 * (1 - e), 0.230, 1.0))

    return col


def sample_legacy(x, y):
    """传统图标：深色圆角底 + 图案。"""
    if round_rect_alpha(x, y, 0.22) <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    t = (x + y) * 0.5
    bg = (0.043 + 0.020 * t, 0.051 + 0.028 * t, 0.075 + 0.045 * t, 1.0)
    return over(bg, content(x, y, 1.0))


def sample_foreground(x, y):
    """自适应图标前景：透明底，图案缩进安全区。"""
    return content(x, y, 0.86)


def render(size, sampler, ss=3):
    w = size * ss
    buf = bytearray(w * w * 4)
    for j in range(w):
        y = (j + 0.5) / w
        base = j * w * 4
        for i in range(w):
            x = (i + 0.5) / w
            c = sampler(x, y)
            o = base + i * 4
            buf[o] = int(max(0.0, min(1.0, c[0])) * 255 + 0.5)
            buf[o + 1] = int(max(0.0, min(1.0, c[1])) * 255 + 0.5)
            buf[o + 2] = int(max(0.0, min(1.0, c[2])) * 255 + 0.5)
            buf[o + 3] = int(max(0.0, min(1.0, c[3])) * 255 + 0.5)

    out = bytearray(size * size * 4)
    norm = float(ss * ss)
    for j in range(size):
        for i in range(size):
            r = g = b = a = 0.0
            for sj in range(ss):
                row = (j * ss + sj) * w * 4
                for si in range(ss):
                    o = row + (i * ss + si) * 4
                    pa = buf[o + 3] / 255.0
                    r += buf[o] * pa
                    g += buf[o + 1] * pa
                    b += buf[o + 2] * pa
                    a += pa
            o = (j * size + i) * 4
            if a > 0:
                out[o] = int(r / a + 0.5)
                out[o + 1] = int(g / a + 0.5)
                out[o + 2] = int(b / a + 0.5)
                out[o + 3] = int(a / norm * 255 + 0.5)
    return out


def main():
    # 传统图标：48/72/96/144/192
    legacy = [('mipmap-mdpi', 48), ('mipmap-hdpi', 72), ('mipmap-xhdpi', 96),
              ('mipmap-xxhdpi', 144), ('mipmap-xxxhdpi', 192)]
    for folder, size in legacy:
        d = os.path.join(OUT, folder)
        os.makedirs(d, exist_ok=True)
        buf = render(size, sample_legacy)
        p = os.path.join(d, 'ic_launcher.png')
        write_png(p, size, size, buf)
        print('%-22s %3d  %6d B' % (folder + '/ic_launcher', size, os.path.getsize(p)))

    # 自适应图标前景：108dp 系列
    fg = [('mipmap-mdpi', 108), ('mipmap-hdpi', 162), ('mipmap-xhdpi', 216),
          ('mipmap-xxhdpi', 324), ('mipmap-xxxhdpi', 432)]
    for folder, size in fg:
        d = os.path.join(OUT, folder)
        os.makedirs(d, exist_ok=True)
        buf = render(size, sample_foreground)
        p = os.path.join(d, 'ic_launcher_foreground.png')
        write_png(p, size, size, buf)
        print('%-22s %3d  %6d B' % (folder + '/ic_launcher_foreground', size, os.path.getsize(p)))


if __name__ == '__main__':
    main()
