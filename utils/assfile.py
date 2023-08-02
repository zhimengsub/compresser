import re
import ass

from utils.fonts import FontChecker


# 是否需要二压
def has_img(asspath) -> bool:
    if not asspath:
        return False
    with open(asspath, 'r', encoding='utf_8_sig') as f:
        while l := f.readline():
            if re.search(r'\\\dimg', l):
                return True
    return False


def check_font_avail(asspath, font_checker: FontChecker) -> list[str]:
    """returns not installed font names"""
    if not asspath:
        return []
    with open(asspath, 'r', encoding='utf_8_sig') as f:
        doc = ass.parse(f)
    fails = []
    for style in doc.styles:
        fontname = style.fontname
        if not font_checker.is_installed(fontname):
            fails.append(fontname)
    return fails

