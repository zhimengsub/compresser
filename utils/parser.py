from utils.subtype import SubType
from utils.vencodertype import VEncType


def parse_subtaskname(subtask_str: str) -> tuple[str, SubType, VEncType, bool]:
    noass = '_noass' in subtask_str
    subtask_str = subtask_str[:-6] if noass else subtask_str
    resl, subname, venc = subtask_str[:-6], subtask_str[-6:-3], subtask_str[-3:]
    subtype = SubType(subname)
    venc = VEncType(venc)
    return resl, subtype, venc, noass
