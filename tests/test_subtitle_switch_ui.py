"""Exercise the actual widget construction with a headless Tk substitute."""
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / 'automation/subtitle-switch'
sys.path.insert(0, str(APP))
import ui_design as design
import switch_app


class Widget:
    widgets = []

    def __init__(self, parent=None, **kw):
        self.parent, self.options = parent, kw
        self.placement, self.tags, self.headings, self.rows = {}, {}, {}, {}
        self.selected = ()
        self.kind = type(self).__name__
        self.tk = types.SimpleNamespace(call=lambda *args: 1.0)
        self.widgets.append(self)

    def pack(self, **kw): self.placement = kw
    def grid(self, **kw): self.placement = kw
    def configure(self, **kw): self.options.update(kw)
    def geometry(self, *args): pass
    def minsize(self, *args): pass
    def title(self, *args): pass
    def option_add(self, *args): self.font = args
    def iconphoto(self, *args): self.icon = args[-1]
    def rowconfigure(self, *args, **kw): pass
    def columnconfigure(self, *args, **kw): pass
    def xview(self, *args): pass
    def yview(self, *args): pass
    def set(self, *args): pass
    def heading(self, key, **kw): self.headings.setdefault(key, {}).update(kw)
    def column(self, key, **kw): pass
    def tag_configure(self, key, **kw): self.tags[key] = kw
    def selection(self): return self.selected
    def selection_set(self, values): self.selected = tuple(values)
    def get_children(self): return tuple(self.rows)
    def delete(self, *args):
        for value in args: self.rows.pop(value, None)
    def insert(self, parent, position, iid, **kw): self.rows[iid] = kw
    def exists(self, key): return key in self.rows
    def see(self, key): self.seen = key
    def get(self, *args): return ''
    def after(self, *args): pass
    def protocol(self, *args): pass
    def bind(self, *args): pass
    def mainloop(self): pass
    def update_idletasks(self): pass
    def winfo_reqwidth(self): return 1200
    def winfo_reqheight(self): return 720


class Variable:
    def __init__(self, value=None): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class Style:
    def __init__(self, *args): pass
    def theme_use(self, *args): pass
    def configure(self, *args, **kw): pass
    def map(self, *args, **kw): pass
    def layout(self, *args, **kw): pass
    def element_create(self, *args, **kw): pass


class UIContractTests(unittest.TestCase):
    def test_local_artwork_has_white_book_pencil_and_red_channel(self):
        app = design.icon_pixels('app', badge=True)
        self.assertEqual(app[0][0], '')
        self.assertEqual(app[10][7], design.WHITE)  # left page
        self.assertEqual(app[14][27], design.WHITE)  # pencil at right
        play = design.icon_pixels('play')
        self.assertEqual(play[16][15], design.WHITE)
        self.assertEqual(play[16][5], design.RED)
        self.assertEqual(len(design.REJECT_REASONS), 8)
        self.assertNotIn('長すぎる', design.REJECT_REASONS)
        self.assertEqual(design.row_tag({'status': 'attention'}), 'attention')
        self.assertEqual(design.row_tag({'status': 'running'}), 'running')

    def test_actual_layout_two_buttons_status_colors_and_icons(self):
        Widget.widgets = []
        tk = types.ModuleType('tkinter')
        ttk = types.ModuleType('tkinter.ttk')
        for name in ('Tk', 'Frame', 'Label', 'Text'):
            setattr(tk, name, type(name, (Widget,), {}))
        for name in ('Frame', 'Label', 'Treeview', 'Scrollbar', 'Combobox', 'Button', 'Checkbutton'):
            setattr(ttk, name, type(name, (Widget,), {}))
        ttk.Style = Style
        tk.StringVar = tk.BooleanVar = Variable
        tk.PhotoImage = lambda **kw: types.SimpleNamespace(put=lambda *a: None)
        tk.ttk = ttk
        tk.messagebox = types.SimpleNamespace(showerror=lambda *a: None, showinfo=lambda *a: None)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'config.json'
            config.write_text(json.dumps({'vault': str(root / 'vault'), 'drive_root': str(root / 'drive'),
                **{key: str(root / key) for key in ('inbox', 'preferences', 'channels')}}), encoding='utf-8')
            with patch.dict(sys.modules, {'tkinter': tk, 'tkinter.ttk': ttk}):
                switch_app.main(config)
        buttons = [w for w in Widget.widgets if w.kind == 'Button']
        saves = [w for w in buttons if w.options.get('text') in ('手動保存', '選択保存')]
        self.assertEqual([w.options['text'] for w in saves], ['手動保存', '選択保存'])
        self.assertIs(saves[0].parent, saves[1].parent)
        question = [w for w in buttons if w.options.get('text') == '保存した動画内容をAIに質問']
        self.assertEqual(len(question), 1)
        self.assertEqual(question[0].options['style'], 'Question.TButton')
        self.assertTrue(all(w.placement['side'] == 'left' for w in saves))
        self.assertTrue(all(w.options['compound'] == 'left' for w in saves))
        self.assertFalse(any(w.options.get('text') == '保存開始' for w in buttons))
        table = next(w for w in Widget.widgets if w.kind == 'Treeview')
        self.assertEqual(table.options['selectmode'], 'extended')
        self.assertEqual(table.tags['attention']['background'], design.PINK)
        self.assertTrue(all('image' in heading for key, heading in table.headings.items() if key != 'checked'))
        self.assertEqual(tuple(table.headings), ('checked',) + tuple(col[0] for col in design.COLUMNS))
        self.assertTrue(any(w.options.get('background') == design.PINK for w in Widget.widgets))
        self.assertEqual(next(w for w in Widget.widgets if w.kind == 'Combobox').options['values'], design.REJECT_REASONS)
        # Empty target callbacks must not instantiate adapters or launch threads.
        with patch('switch_app.Services') as service, patch('switch_app.threading.Thread') as thread:
            for button in saves: button.options['command']()
            service.assert_not_called()
            thread.assert_not_called()
