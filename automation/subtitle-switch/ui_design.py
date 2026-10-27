"""Local pixel artwork and layout constants; no downloads or GUI on import."""
import math
RED = '#ed2338'
PINK = '#ffe8ed'
WHITE = '#ffffff'
BACKGROUND = '#f6f7f9'
REJECT_REASONS = ('興味なし', 'もう知ってる', '重複', '古い', '浅い', '宣伝っぽい', '英語・言語の壁', 'あとで')
COLUMNS = (
    ('title', 'タイトル', 'document', 250),
    ('channel', 'チャンネル', 'play', 145),
    ('published_at', '公開日', 'calendar', 115),
    ('lang', '言語', 'globe', 65),
    ('theme', 'テーマ', 'tag', 100),
    ('reason', '理由', 'bulb', 130),
    ('stage', '工程', 'gear', 125),
    ('status', '状態／待ち理由', 'wave', 450),
    ('notebook', 'Notebook使用数', 'notebook', 155),
)
SAVE_BUTTONS = (('manual', '手動保存'), ('selected', '選択保存'))


def row_tag(row):
    return 'attention' if row['status'] in ('attention', 'waiting') else 'running' if row['status'] == 'running' else ''


def icon_pixels(kind, size=32, badge=False):
    """Rasterize simple original vector shapes, returning transparent pixel rows."""
    pixels = [['' for _ in range(size)] for _ in range(size)]
    ink = WHITE if badge else RED

    def polygon(points, color):
        for py in range(size):
            y = (py + .5) * 32 / size
            for px in range(size):
                x = (px + .5) * 32 / size
                inside = False
                j = len(points) - 1
                for i, (xi, yi) in enumerate(points):
                    xj, yj = points[j]
                    if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                        inside = not inside
                    j = i
                if inside:
                    pixels[py][px] = color

    def rect(x, y, w, h, color=ink):
        polygon([(x,y), (x+w,y), (x+w,y+h), (x,y+h)], color)

    if badge or kind == 'play':
        polygon([(5,1),(27,1),(31,5),(31,27),(27,31),(5,31),(1,27),(1,5)], RED)
    if kind in ('book', 'app'):
        # Open pages on the left, a separate diagonal writing pencil on the right.
        polygon([(5,8),(10,7),(15,9),(15,25),(10,23),(5,24)], ink)
        polygon([(16,9),(20,7),(22,8),(22,23),(16,25)], ink)
        # Two page accents and a central gutter retain the open-book outline.
        page_line = RED if badge else WHITE
        polygon([(8,11),(11,10),(13,11),(13,12),(11,11),(8,12)], page_line)
        polygon([(8,15),(11,14),(13,15),(13,16),(11,15),(8,16)], page_line)
        polygon([(18,11),(20,10),(21,10),(21,11),(18,12)], page_line)
        polygon([(25,19),(27,20),(31,10),(29,9)], ink)
        polygon([(25,20),(27,21),(24,23)], ink)
    elif kind == 'play':
        polygon([(12,8),(25,16),(12,24)], WHITE)
    elif kind == 'spark':
        polygon([(16,2),(19,12),(29,16),(19,19),(16,30),(13,19),(3,16),(13,12)], '#e87824')
    elif kind == 'robot':
        polygon([(5,8),(27,8),(29,11),(29,25),(26,28),(6,28),(3,25),(3,11)], '#222222')
        rect(9,14,4,4,WHITE); rect(19,14,4,4,WHITE)
        rect(10,22,12,2,WHITE); rect(15,3,2,5,'#222222')
    elif kind == 'wave':
        polygon([(2,16),(8,16),(12,4),(17,26),(21,14),(30,14),(30,17),(23,17),(17,31),(12,13),(10,19),(2,19)], ink)
    elif kind == 'tag':
        polygon([(4,5),(17,5),(29,17),(17,29),(4,16)], ink)
        rect(8,9,4,4,WHITE)
    elif kind == 'bulb':
        polygon([(10,4),(22,4),(27,10),(24,18),(21,22),(11,22),(8,18),(5,10)], ink)
        rect(12,24,8,3); rect(14,28,4,2)
    elif kind == 'gear':
        # Circular hub and eight identical radial teeth.
        for py in range(size):
            for px in range(size):
                x = (px + .5) * 32 / size - 16
                y = (py + .5) * 32 / size - 16
                radius = math.hypot(x, y)
                angle = math.atan2(y, x)
                tooth = abs(((angle + math.pi / 8) % (math.pi / 4)) - math.pi / 8) < .15
                if 5 <= radius <= (14 if tooth else 11):
                    pixels[py][px] = ink
    elif kind == 'globe':
        polygon([(11,2),(21,2),(29,10),(29,22),(21,30),(11,30),(3,22),(3,10)], ink)
        rect(7,8,18,16,WHITE); rect(14,3,3,27); rect(4,14,24,3)
    elif kind == 'skip':
        polygon([(3,7),(16,16),(3,25)], ink); polygon([(16,7),(29,16),(16,25)], ink)
    elif kind in ('back', 'refresh'):
        for py in range(size):
            for px in range(size):
                x = (px + .5) * 32 / size - 16
                y = (py + .5) * 32 / size - 16
                r = math.hypot(x, y)
                if 9 <= r <= 12 and not (x < -4 and y > 0):
                    pixels[py][px] = ink
        polygon([(2,13),(9,7),(9,17)], ink)
        if kind == 'refresh':
            polygon([(30,19),(23,25),(23,15)], ink)
    elif kind == 'info':
        polygon([(10,2),(22,2),(30,10),(30,22),(22,30),(10,30),(2,22),(2,10)], RED)
        rect(14,7,4,4,WHITE); rect(14,14,4,12,WHITE)
    else:
        rect(6,5,21,25); rect(9,10,15,16,WHITE)
        if kind == 'calendar':
            rect(9,2,3,7); rect(21,2,3,7); rect(9,12,15,3)
        else:
            rect(11,14,10,2); rect(11,19,8,2)
    return pixels


def minimum_control_height(font_linespace, image_height=0, padding=12):
    return max(font_linespace, image_height) + 2 * padding


def photo(tk, master, kind, size=32, badge=False):
    image = tk.PhotoImage(master=master, width=size, height=size)
    scale = 3
    pixels = icon_pixels(kind, size * scale, badge)
    for y in range(size):
        for x in range(size):
            samples = [pixels[y * scale + dy][x * scale + dx] for dy in range(scale) for dx in range(scale)]
            colors = [c for c in samples if c]
            if colors:
                # Composite edge pixels against the light surface to smooth the silhouette.
                colors += [WHITE] * (scale * scale - len(colors))
                rgb = [sum(int(c[i:i+2], 16) for c in colors) // len(colors) for i in (1, 3, 5)]
                image.put('#%02x%02x%02x' % tuple(rgb), (x, y))
    return image


def rounded_photo(tk, master, color, size=40, radius=10):
    """Small nine-slice background with supersampled rounded corners."""
    image = tk.PhotoImage(master=master, width=size, height=size)
    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    for y in range(size):
        for x in range(size):
            inside = 0
            for dy in range(3):
                for dx in range(3):
                    px, py = x + (dx + .5) / 3, y + (dy + .5) / 3
                    cx = min(max(px, radius), size - radius)
                    cy = min(max(py, radius), size - radius)
                    inside += (px - cx) ** 2 + (py - cy) ** 2 <= radius ** 2
            if inside:
                mixed = tuple((c * inside + 255 * (9 - inside)) // 9 for c in rgb)
                image.put('#%02x%02x%02x' % mixed, (x, y))
    return image
