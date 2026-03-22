def alpha_folder(game_name: str) -> str:
    """Return the alphabetical subfolder for a given game name."""
    stripped = game_name.lstrip()
    if not stripped:
        return "#"
    first = stripped[0]
    return first.upper() if first.isalpha() else "#"
