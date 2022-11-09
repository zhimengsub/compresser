import enum

class SubType(enum.Enum):
    SJ = 'chs'
    TJ = 'cht'

    def get_name(self):
        if self.name == 'SJ':
            return '简日双语'
        if self.name == 'TJ':
            return '繁日双语'

    def simp_name(self):
        return self.get_name()[:2]
