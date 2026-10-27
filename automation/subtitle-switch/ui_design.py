"""Local pixel artwork and layout constants; no downloads or GUI on import."""
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
        polygon([(16,9),(21,7),(24,8),(20,13),(19,23),(16,25)], ink)
        polygon([(21,21),(24,21),(30,11),(27,9)], ink)
        polygon([(20,22),(23,23),(20,26)], ink)
    elif kind == 'play':
        polygon([(12,8),(25,16),(12,24)], WHITE)
    elif kind == 'wave':
        polygon([(2,16),(8,16),(12,4),(17,26),(21,14),(30,14),(30,17),(23,17),(17,31),(12,13),(10,19),(2,19)], ink)
    elif kind == 'tag':
        polygon([(4,5),(17,5),(29,17),(17,29),(4,16)], ink)
        rect(8,9,4,4,WHITE)
    elif kind == 'bulb':
        polygon([(10,4),(22,4),(27,10),(24,18),(21,22),(11,22),(8,18),(5,10)], ink)
        rect(12,24,8,3); rect(14,28,4,2)
    elif kind == 'gear':
        polygon([(12,2),(20,2),(21,7),(27,7),(30,14),(26,19),(27,25),(20,28),(15,25),(8,28),(4,21),(7,16),(3,10),(9,6)], ink)
        rect(12,12,8,8,WHITE)
    elif kind == 'globe':
        polygon([(11,2),(21,2),(29,10),(29,22),(21,30),(11,30),(3,22),(3,10)], ink)
        rect(7,8,18,16,WHITE); rect(14,3,3,27); rect(4,14,24,3)
    elif kind == 'skip':
        polygon([(3,7),(16,16),(3,25)], ink); polygon([(16,7),(29,16),(16,25)], ink)
    elif kind in ('back', 'refresh'):
        polygon([(2,13),(13,3),(13,10),(25,10),(30,16),(30,26),(25,21),(23,16),(13,16),(13,23)], ink)
        if kind == 'refresh':
            polygon([(2,24),(8,28),(21,28),(24,23),(8,23),(8,19)], ink)
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


def photo(tk, master, kind, size=32, badge=False):
    image = tk.PhotoImage(master=master, width=size, height=size)
    for y, row in enumerate(icon_pixels(kind, size, badge)):
        for x, color in enumerate(row):
            if color:
                image.put(color, (x, y))
    return image
