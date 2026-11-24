#!/usr/bin/env python3
"""Build docs/en/index.html from the Ukrainian source docs/index.html.

The Ukrainian page is the single source of truth for code and design.
This script swaps every user-facing string for its English version.
It fails loudly when a source string is missing (so a changed Ukrainian
text never silently stays untranslated) and when any Cyrillic is left over.

Run:  python3 scripts/build_en.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "index.html"
OUT = ROOT / "docs" / "en" / "index.html"
BASE = "https://calmnessuniverse.art/graditxt/"

UK_DESC = ("Градітекст перетворює будь-який текст (до 600 знаків) на градієнтне полотно: кожна літера має "
           "власний градієнт, між знаками — плавні конектори. Формати 1:1, 4:5, 16:9, 9:16, анімація і "
           "збереження картинки чи відео. Безкоштовно, просто в браузері.")
EN_DESC = ("Graditext turns any text (up to 600 characters) into a gradient canvas: every letter has its own "
           "gradient, with smooth connectors between signs. 1:1, 4:5, 16:9 and 9:16 formats, animation, "
           "image and video export. Free, right in your browser.")

# (ukrainian, english) — applied in order, every occurrence; longer / more specific strings first.
PAIRS = [
    # ---- head / SEO ----
    ('<html lang="uk"', '<html lang="en"'),
    ('<title>Градітекст — текст у градієнтне полотно</title>', '<title>Graditext — text into a gradient canvas</title>'),
    (UK_DESC, EN_DESC),
    (f'<link rel="canonical" href="{BASE}">', f'<link rel="canonical" href="{BASE}en/">'),
    (f'<meta property="og:url" content="{BASE}">', f'<meta property="og:url" content="{BASE}en/">'),
    ('<meta property="og:locale" content="uk_UA">', '<meta property="og:locale" content="en_US">'),
    ('Будь-який текст — у градієнтне полотно: кожна літера має власний градієнт.',
     'Any text, turned into a gradient canvas: every letter has its own gradient.'),
    ('Слово «Градітекст», кожна літера якого залита своїм градієнтом',
     'The word Graditext in Ukrainian, each letter filled with its own gradient'),
    (f'"url":"{BASE}","inLanguage":"uk"', f'"url":"{BASE}en/","inLanguage":"en"'),
    ('<a class="lang" href="en/" hreflang="en" lang="en" title="English">EN</a>',
     '<a class="lang" href="../" hreflang="uk" lang="uk" title="Українська">UA</a>'),

    # ---- page ----
    ('</span> Анімувати', '</span> Animate'),
    ('</span> Зупинити', '</span> Stop'),
    ('Текст стає полотном. Кожен знак має свій градієнт, а між знаками стоять м’які конектори.',
     'Text becomes a canvas. Every sign has its own gradient, joined to the next by soft connectors.'),
    ('<label for="txt">Текст ', '<label for="txt">Text '),
    ('spellcheck="false">Світло — це ти 🫶🏻</textarea>', 'spellcheck="false">You are the light 🫶🏻</textarea>'),
    ('<label>Формат</label>', '<label>Format</label>'),
    ('<label>Шлях</label>', '<label>Path</label>'),
    ('>Змійка<', '>Snake<'),
    ('>Рядки<', '>Rows<'),
    ('<label>Паузи</label>', '<label>Pauses</label>'),
    ('>Темні<', '>Dark<'),
    ('>Світлі<', '>Light<'),
    ('Ширина знака', 'Sign width'),
    ('М’якість між рядками', 'Softness between rows'),
    ('Пульс (тінь на межі рядків)', 'Pulse (shadow at row edges)'),
    ('Об’єм (вертикальний нахил)', 'Depth (vertical tilt)'),
    ('<label for="grain">Зерно ', '<label for="grain">Grain '),
    ('Палітра (seed)', 'Palette (seed)'),
    ('title="Випадкова палітра">Перемішати<', 'title="Random palette">Shuffle<'),
    ('>Літери<', '>Letters<'),
    ('Зберегти PNG (3000 px)', 'Save PNG (3000 px)'),
    ('Швидкість руху', 'Motion speed'),
    ('Амплітуда руху', 'Motion amplitude'),
    ('<label>Якість відео</label>', '<label>Video quality</label>'),
    ('<label>Початок відео</label>', '<label>Video start</label>'),
    ('>Безшовний луп<', '>Seamless loop<'),
    ('>Плавний вхід<', '>Smooth intro<'),
    ('>Відео 6 с<', '>Video 6 s<'),
    ('>Відео 12 с<', '>Video 12 s<'),
    ('<label>Знаки цього тексту</label>', '<label>Signs in this text</label>'),
    ('<summary>Як працюють конектори</summary>', '<summary>How connectors work</summary>'),

    # ---- connector rules ----
    ('<code>літера → літера</code>: світловий шов, тобто суміш кінця першої й початку наступної з легким підсиленням насиченості',
     '<code>letter → letter</code>: a seam of light, blending the end of one letter into the start of the next with a slight boost in saturation'),
    ('<code>пробіл</code>: подих, кольори сусідів тьмяніють і тонуть у фоні пауз',
     '<code>space</code>: a breath, neighboring colors fade and sink into the pause tone'),
    ('<code>¶ новий рядок</code>: довгий, глибший подих', '<code>¶ line break</code>: a longer, deeper breath'),
    ('</code> вузол: різке затягування в найглибший тон', '</code> knot: a sharp pull into the deepest tone'),
    ('</code> м’яке занурення, коротша пауза', '</code> soft dip, a shorter pause'),
    ('</code> спалах: майже білий центр, насичені фланги', '</code> flash: an almost white core with saturated flanks'),
    ('</code> поворот: колір обертається у протилежний відтінок', '</code> turn: the color rotates to its opposite hue'),
    ('</code> пульс: два удари довкола тіні', '</code> pulse: two beats around a shadow'),
    ('</code> міст: чиста інтерполяція, тире ще й трохи підсвічене', '</code> bridge: pure interpolation, dashes are slightly lit too'),
    ('</code> відблиск: вузька бліда іскра', '</code> glint: a narrow pale spark'),
    ('</code> тінь: затемнений перехід', '</code> shade: a darkened transition'),
    ('</code> три маленькі вузли', '</code> three small knots'),
    ('Кожна літера має три кольорові точки (вхід, серце, вихід) і вертикальний нахил. Усе це береться з її коду й seed. '
     'Велика літера насиченіша й контрастніша за малу, а нахил у неї протилежний. '
     'Усі змішування йдуть в OKLab, по шляху працює кубічна Ерміт-інтерполяція.',
     'Each letter has three color points (in, heart, out) and a vertical tilt, all derived from its code point and the seed. '
     'An uppercase letter is more saturated and contrasting than its lowercase, with the tilt reversed. '
     'All blending happens in OKLab, and a cubic Hermite interpolation runs along the path.'),

    # ---- script: sign labels ----
    ("'градієнт знака'", "'sign gradient'"),
    ("'пробіл: подих'", "'space: breath'"),
    ("'новий рядок: довгий подих'", "'line break: long breath'"),
    ("'крапка з комою: пульс і відлуння'", "'semicolon: pulse and echo'"),
    ("'крапка: вузол'", "'period: knot'"),
    ("'кома: м’яке занурення'", "'comma: soft dip'"),
    ("'знак оклику: спалах'", "'exclamation mark: flash'"),
    ("'знак питання: поворот'", "'question mark: turn'"),
    ("'двокрапка: пульс'", "'colon: pulse'"),
    ("'дефіс: міст'", "'hyphen: bridge'"),
    ("'тире: світлий міст'", "'dash: bright bridge'"),
    ("'лапки/апостроф: відблиск'", "'quotes/apostrophe: glint'"),
    ("'дужка: тінь'", "'bracket: shade'"),
    ("'три крапки: три вузли'", "'ellipsis: three knots'"),
    ("`«${disp}» · ", "`“${disp}” · "),

    # ---- script: status texts ----
    ("'безшовний луп.'", "'seamless loop.'"),
    ("'рух прокидається за 2 с.'", "'motion wakes up over 2 s.'"),
    ("'Рендеринг…'", "'Rendering…'"),
    ("'Не вдалося завантажити mp4-muxer'", "'Could not load mp4-muxer'"),
    ("const vidLabel = b => `Відео ${b.dataset.sec} с`;", "const vidLabel = b => `Video ${b.dataset.sec} s`;"),
    ("'Цей браузер не вміє кодувати відео (WebCodecs). Спробуй свіжий Chrome, Edge чи Safari.'",
     "'This browser cannot encode video (WebCodecs). Try a recent Chrome, Edge or Safari.'"),
    ("'Підготовка…'", "'Preparing…'"),
    ("'Браузер не підтримує H.264 для такого розміру'", "'This browser does not support H.264 at this size'"),
    ("`Скасувати · ${pct}%`", "`Cancel · ${pct}%`"),
    ("'Збираю файл…'", "'Building file…'"),
    ("`Готово: ${W}×${H}, ${fps} кадрів/с, ${sec} с, ${(blob.size / 1048576).toFixed(1)} МБ.`",
     "`Done: ${W}×${H}, ${fps} fps, ${sec} s, ${(blob.size / 1048576).toFixed(1)} MB.`"),
    ("'Не вийшло: '", "'Failed: '"),
    ("'Скасовано.'", "'Cancelled.'"),
    ("Intl.Segmenter('uk'", "Intl.Segmenter('en'"),

    # ---- generic, last ----
    ('кадрів/с', 'fps'),
    ('Градітекст', 'Graditext'),
]


def main() -> int:
    s = SRC.read_text(encoding="utf-8")
    missing = [uk for uk, _ in PAIRS if uk not in s]
    if missing:
        print("These Ukrainian strings are no longer in docs/index.html, update scripts/build_en.py:", file=sys.stderr)
        for m in missing:
            print("  -", m[:100], file=sys.stderr)
        return 1
    for uk, en in PAIRS:
        s = s.replace(uk, en)
    left = [(n, line.strip()[:120]) for n, line in enumerate(s.splitlines(), 1)
            if re.search(r"[А-Яа-яІіЇїЄєҐґ]", line) and 'title="Українська">UA<' not in line]
    if left:
        print("Untranslated Cyrillic left in the English page:", file=sys.stderr)
        for n, line in left:
            print(f"  {n}: {line}", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(s, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
