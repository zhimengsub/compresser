import enum

class VEncType(enum.Enum):
    X265 = '265'
    X264 = '264'

    def get_vtype_name(self):
        if self.value == '265':
            return 'HEVC'
        if self.value == '264':
            return 'AVC'

    def get_venc_name(self):
        return self.value

    def get_conf_venc_name(self):
        return 'x' + self.value

    def is264(self):
        return self == VEncType.X264

    def is265(self):
        return self == VEncType.X265
