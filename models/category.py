from typing import List


class Category:
    def __init__(self, id_: str, name: str, types: List[str]):
        self.id = id_
        self.name = name
        self.types = types  # essencial, opcional, fixa, compartilhada
