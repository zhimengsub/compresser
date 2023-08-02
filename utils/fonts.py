import win32com.client
import re


class FontChecker:
    types = ['粗体', '半粗体', '常规', '中等', '细体', 'Bold', 'Regular', 'Normal', 'W']
    pat_types = '(?:' + '|'.join(types) + ')'

    def __init__(self):
        shell = win32com.client.Dispatch("Shell.Application")
        fonts_folder = shell.Namespace(0x14)
        self.font_names = [item.Name for item in fonts_folder.Items()]

    @staticmethod
    def _equal(name1: str, name2: str) -> bool:
        name1 = name1.removeprefix('@')
        name2 = name2.removeprefix('@')
        name1 = re.sub(' ' + FontChecker.pat_types, '', name1)
        name2 = re.sub(' ' + FontChecker.pat_types, '', name2)
        return name1 == name2

    def is_installed(self, font_name) -> bool:
        for name in self.font_names:
            if FontChecker._equal(name, font_name):
                return True
        return False

