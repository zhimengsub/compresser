import enum

class SubType(enum.Enum):
    SJ = 'chs'
    TJ = 'cht'
    # add two noass types for compatability
    SJ_NOASS = 'chs_noass'
    TJ_NOASS = 'cht_noass'

    def is_SJ(self):
        return self.name.startswith('SJ')
    def is_TJ(self):
        return self.name.startswith('TJ')

    def get_name(self):
        if self.name.startswith('SJ'):
            return '简日双语'
        if self.name.startswith('TJ'):
            return '繁日双语'

    def simp_name(self):
        return self.get_name()[:2]
