from init_db import reset_db, seed_pluggy_items


def reset_and_reseed():
    """Dropa e recria todas as tabelas, depois faz seed dos pluggy_items."""
    reset_db()
    seed_pluggy_items()
