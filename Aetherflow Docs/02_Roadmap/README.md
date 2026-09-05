# AetherFlow — Полный план разработки

## Структура версий

Проект развивается по крупным фазам. Версии **0.6.x** предназначены только для Blender / Python / процедурной генерации и подготовки игровой карты. Начиная с **0.7.0** начинается интеграция в Unreal Engine 5.

Главный принцип: существующий код не переписывается без необходимости. Каждая следующая версия расширяет и проверяет уже работающую систему.

---

# ФАЗА 1 — BLENDER / PYTHON / ИГРОВАЯ КАРТА

## v0.6.1 — ТЕКУЩАЯ БАЗА

Исходная рабочая версия процедурной карты.

Уже реализовано:

- процедурная генерация сцены;
- процедурный рельеф и heightmap;
- игровая область 200 × 200 м;
- внешний пол 220 × 220 м;
- 5 точек захвата;
- 2 базы;
- дороги и рампы;
- центральная зона Aether Altar / Aether Crown;
- AetherCore;
- 4 gameplay pockets;
- система укрытий и анализ прямой видимости;
- процедурные камни;
- навигационная сетка;
- внешняя граница;
- детерминированная симуляция;
- валидация;
- экспорт map_data.json.

**Важно:** v0.6.1 не переделывается с нуля. Следующие версии используют её как зафиксированный фундамент.

---

# v0.6.2 — GAMEPLAY DRESSING + ENVIRONMENT + INTERACTION FOUNDATION

Главная задача — превратить каркас v0.6.1 в полноценное игровое пространство без изменения фундаментальной топологии.

Реализованные/прорабатываемые подсекции включают baseline lock, Gameplay Cover 2.0, expanded rock system, natural environment integration, environment distribution, gameplay-aware vegetation, objective dressing, capture interaction/UI foundation, base shop/dressing, unified gameplay markers, AetherCore dressing, environment safety, deterministic environment, export extension и final validation.

## v0.6.2.1 — GAMEPLAY COVER 2.0 + ALTAR HARDENING

- тактическое укрытие objectives и pockets;
- контроль CoreCover вокруг AetherCore;
- четыре строгих симметричных Altar protector-а на N/E/S/W;
- реальная adjacent-objective macro rotation;
- проверка navigation и mesh intersections.

---

# v0.6.3 — TERRAIN + ROADS + RAMPS + POCKETS + COMBAT SPACE REFINEMENT

### Главная задача

Доработать физическое игровое пространство только там, где тесты показывают реальные проблемы. Топология и расположение баз/objectives не должны дрейфовать.

## v0.6.3.1 — TERRAIN REFINEMENT — IN PROGRESS

### Реализовано

- новый `core/terrain_refinement.py` с общим bounded-профилем;
- AetherCore: более читаемая центральная депрессия;
- Crown: усилена положительная высота;
- WestMonolith/EastMonolith: одинаково усилены возвышения;
- SouthRift: контролируемо усилена депрессия;
- центральный transition radius немного расширен для плавности;
- новый terrain slope audit в pipeline;
- target maximum sampled terrain slope `< 35°`;
- objective/base XY координаты не меняются;
- topology не меняется;
- версия проекта поднята до `0.6.3.1`.

### Validation gate

После fresh Blender 5.2 run должны сохраняться:

- navigation problems = 0;
- 4/4 pockets reachable;
- evaluated-mesh intersections = 0;
- 4 Altar protectors, центрированные и симметричные;
- существующая Blue/Red fairness не деградирует;
- terrain slope audit = PASS;
- pipeline проходит все 10 stages.

## v0.6.3.2 — HEIGHT TRANSITIONS

Проверить slope, ramps, walkability, minion traversal, LOS changes и combat readability. Исправлять только реальные проблемы.

## v0.6.3.3 — ROAD NETWORK REFINEMENT

Проверить base → objective, objective → objective, outer/inner rotation, flank, pocket и retreat routes. Не создавать классические три MOBA lanes.

## v0.6.3.4 — RAMP REFINEMENT

Проверить существующие рампы для героя, minion, группы и 5 игроков. Исправлять только узкие, слишком крутые или плохо читаемые переходы.

## v0.6.3.5 — POCKET REFINEMENT

Проверить West/East/SW/SE pockets, сохранив их функцию flank / ambush / retreat.

## v0.6.3.6 — COMBAT COVER REFINEMENT

Использовать существующий cover optimizer только для реально проблемных зон.

## v0.6.3.7 — COMBAT SPACE TESTING

Сценарии: 1v1, 2v2, 3v3, 5v5, retreat, flank, interception, objective defense, objective assault.

## v0.6.3.8 — DEATHBALL MITIGATION

При подтверждённой проблеме использовать flank routes, split routes, interception paths, LOS breaks и controlled choke points.

---

# v0.6.4 — BOUNDARY + ENVIRONMENT + RESOURCES

Расширение внешней среды, ресурсов и проверки игровых границ после завершения terrain/combat-space refinement.

# v0.6.5 — FULL DOMINION SIMULATION + MAP BALANCE

Полная детерминированная симуляция 5v5, баланс objectives, rotation, comeback, deathball, snowball и time-to-objective.

# v0.6.6 — FINAL VALIDATION + EXPORT + MAP LOCK

Финальная проверка Blender-карты и фиксация MAP LOCK перед UE5.

# v0.7.0 — UNREAL ENGINE 5 FOUNDATION

После MAP LOCK начинается интеграция игрового runtime в UE5.
