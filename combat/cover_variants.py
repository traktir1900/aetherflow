# Модуль вариативности форм укрытий (v0.5.2.4)

COVER_LIBRARY = {
    "LOW": [
        "Boulder",
        "Debris",
        "RuinedPillar"
    ],
    "MEDIUM": [
        "L_Wall",
        "HalfWall",
        "BrokenBarrier"
    ]
}

def select_cover_variant(cover_type, intent, index=0):
    variants = COVER_LIBRARY.get(cover_type, ["HalfWall"])
    # Процедурный детерминированный выбор по индексу
    return variants[index % len(variants)]
