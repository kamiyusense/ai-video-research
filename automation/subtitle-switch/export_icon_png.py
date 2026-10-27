"""Export original icon artwork as PNG without extra packages or a display."""
import argparse
import struct
import zlib
from pathlib import Path

import ui_design


def write_png(path, pixels):
    height, width = len(pixels), len(pixels[0])
    rows = bytearray()
    for row in pixels:
        rows.append(0)
        for color in row:
            rows.extend(bytes.fromhex(color[1:]) + b'\xff' if color else b'\x00\x00\x00\x00')
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', width, height, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')
    Path(path).write_bytes(png)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kind')
    parser.add_argument('output')
    parser.add_argument('--badge', action='store_true')
    args = parser.parse_args()
    write_png(args.output, ui_design.icon_pixels(args.kind, 128, args.badge))


if __name__ == '__main__':
    main()
