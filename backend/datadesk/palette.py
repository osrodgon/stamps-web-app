"""Stable pastel tone per colour name.

The workspace paints every stamp colour as a chip. The mockup assigned four
hand-picked palettes; here the tone is derived from the name so the same colour
looks the same on every screen and in both languages, and adding a colour to the
catalogue needs no code change.

The names are catalogue data, not interface text: they are Spanish because the
database is, so the keyword map is in Spanish too. Keywords are stems, not whole
words, and they are checked in order, so a compound name keeps its dominant
colour ("Azul verdoso" is blue, "Verde oliva" is green).
"""
import hashlib
import unicodedata

TONES: tuple[str, ...] = (
    "red",
    "blue",
    "green",
    "amber",
    "brown",
    "grey",
    "purple",
    "orange",
)
"""The pastel palettes available to the chips (see ``datadesk.css``)."""

KEYWORDS: tuple[tuple[str, str], ...] = (
    # "Multicolor" and "Cuatricomía" are the two most common values in the
    # catalogue: they read as "not one colour", so they get the neutral tone
    # instead of a random one.
    ("multi", "grey"),
    ("cuatri", "grey"),
    ("azul", "blue"),
    ("celeste", "blue"),
    ("verd", "green"),
    ("oliv", "green"),
    ("esmeralda", "green"),
    # Brown shades are checked before red: "Castaño rojizo" and "Sepia rojo"
    # read as brown, not as a bright red.
    ("sepia", "brown"),
    ("marron", "brown"),
    ("castan", "brown"),
    ("tierra", "brown"),
    ("bronce", "brown"),
    ("cobre", "brown"),
    ("beige", "brown"),
    ("carm", "red"),
    ("roj", "red"),
    ("escarlata", "red"),
    ("granate", "red"),
    ("rosa", "red"),
    ("amarill", "amber"),
    ("ocre", "amber"),
    ("dorad", "amber"),
    ("oro", "amber"),
    ("ambar", "amber"),
    ("crema", "amber"),
    ("naranja", "orange"),
    ("violeta", "purple"),
    ("morad", "purple"),
    ("lila", "purple"),
    ("purpur", "purple"),
    ("negr", "grey"),
    ("gris", "grey"),
    ("plata", "grey"),
    ("blanc", "grey"),
)
"""Keyword stem → tone, first match wins."""


def tone_for(name: str) -> str:
    """Returns the tone of a colour name, stable across processes.

    The fallback hash uses md5 rather than Python's ``hash()`` on purpose: the
    built-in is salted per process, so the same colour would change tone after a
    restart or between gunicorn workers.
    """
    key = _normalise(name)
    for keyword, tone in KEYWORDS:
        if keyword in key:
            return tone

    digest = hashlib.md5(key.encode("utf-8")).digest()
    return TONES[digest[0] % len(TONES)]


def _normalise(name: str) -> str:
    """Lowercases a name and strips its accents."""
    decomposed = unicodedata.normalize("NFKD", name or "")
    return "".join(
        char for char in decomposed if not unicodedata.combining(char)
    ).lower()
