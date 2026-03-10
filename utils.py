def string_to_boolean_map(s: str) -> bool | None:
    bool_map = {"yes": True, "y": True, "no": False, "n": False, "true": True, "false": False, "1": True, "0": False}
    normalized_s = s.strip().lower()
    return bool_map.get(normalized_s)
