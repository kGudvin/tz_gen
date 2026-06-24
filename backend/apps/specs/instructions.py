DEFAULT_MUTABLE_INSTRUCTION = "Участник закупки указывает в заявке конкретное значение характеристики"
DEFAULT_IMMUTABLE_INSTRUCTION = "Значение характеристики не может изменяться участником закупки"


def instruction_for_unit(unit_name: str, saved_instruction: str = "") -> str:
    if not (unit_name or "").strip():
        return DEFAULT_IMMUTABLE_INSTRUCTION
    return saved_instruction or DEFAULT_MUTABLE_INSTRUCTION
