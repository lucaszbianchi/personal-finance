class Person:
    def __init__(self, person_id: str, name: str, split_info: dict | None = None):
        self.person_id = person_id
        self.name = name
        # Normaliza split_info para sempre ser um dict mutável
        self.split_info = split_info if split_info is not None else {}

    def is_partner(self) -> bool:
        return self.split_info.get("is_partner") is True

    def settled_up(self) -> bool:
        return bool(self.split_info.get("settled_up"))

    def mark_settled(self):
        self.split_info["settled_up"] = True
