import math
from mathutils import Vector

def calculate_cover_rotation(cand_pos, threat_pos, intent):
    # Вектор от позиции кандидата к источнику угрозы / цели защиты
    dx = threat_pos[0] - cand_pos[0]
    dy = threat_pos[1] - cand_pos[1]
    base_angle = math.degrees(math.atan2(dy, dx))
    
    # Коррекция ориентации в зависимости от Intent (Cover Facing Vector)
    if intent == "ANTI_SNIPER":
        # Разворачиваем защитную стену перпендикулярно оси обстрела (+90 градусов)
        return (base_angle + 90.0) % 360.0
    elif intent in ["FLANK_SUPPORT", "ROTATION_ASSIST"]:
        # Параллельное или скошенное укрытие для движения вдоль него
        return (base_angle + 45.0) % 360.0
    elif intent == "OBJECTIVE_DEFENSE":
        return base_angle % 360.0
    else:
        return (base_angle + 15.0) % 360.0
