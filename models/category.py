class Category:
    def __init__(
        self,
        id_: str,
        description: str,
        description_translated: str = None,
        parent_id: str = None,
        parent_description: str = None,
        expense_type: str = None,
    ):
        self.id = id_
        self.description = description
        self.description_translated = description_translated
        self.parent_id = parent_id
        self.parent_description = parent_description
        self.expense_type = expense_type  # 'necessary' | 'optional' | None (defaults to optional)
