# AetherFlow — Полный план разработки

## Структура версий

Проект развивается по крупным фазам. Версии **0.6.x** предназначены только для Blender / Python / процедурной генерации и подготовки игровой карты. Начиная с **0.7.0** начинается интеграция в Unreal Engine 5.

Главный принцип: существующий код не переписывается без необходимости. Каждая следующая версия расширяет и проверяет уже работающую систему.

---

# ФАЗА 1 — BLENDER / PYTHON / ИГРОВАЯ КАРТА

## v0.6.1 — БАЗА

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

v0.6.1 используется как зафиксированный фундамент для последующих refinement-версий.

---

# v0.6.2 — GAMEPLAY DRESSING + ENVIRONMENT + INTERACTION FOUNDATION

Главная задача — превратить каркас v0.6.1 в полноценное игровое пространство без изменения фундаментальной топологии.

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

## v0.6.3.1 — TERRAIN REFINEMENT — CLOSED

Baseline зафиксирован: Blue/Red fairness = 0.0%, 5/5 objectives, 4/4 pockets reachable, navigation problems = 0, evaluated-mesh intersections = 0, gameplay symmetry = PASS. XY bases/objectives frozen.

## v0.6.3.2 — HEIGHT TRANSITIONS — IMPLEMENTED / TECHNICAL CLOSURE CARRIED INTO v0.6.4

Система высотных переходов и minion traversal audit реализованы. Последний supplied runtime показал dedicated minion traversal **PASS** для обеих зеркальных сценариев, но общий Stage 9 validation завершился `FAILED` из-за технических validation/model issues и Crown structural-overlap warnings.

Общие правила остаются:

- combat slope <= 15°;
- minion-safe slope <= 18°;
- walkable <= 25°;
- ramp <= 30°;
- hard terrain ceiling = 35°;
- adjacent height step <= 0.75 м;
- minion corridor target = 1.30 м;
- group/ramp width target = 4.0 м.

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

# v0.6.4 — BOUNDARY + ENVIRONMENT + RESOURCES — CURRENT

### Главная задача

Закрыть внешний периметр, корректно оформить Crown/Boundary interaction, завершить визуальную presentation layer для capture objectives и подготовить среду/resources без нарушения gameplay contract.

### Реализовано

- global elliptical outer boundary;
- intentional Crown north-wall opening;
- Crown Sanctum presentation contract с lower throne plate only;
- отдельный Crown capture button и capture indicator ring;
- raised-platform-aware Crown capture presentation;
- two visual-only Crown capture links to adjacent objectives;
- road center light guides;
- capture-button route binding;
- runtime validation compatibility для visual-only guides и dedicated boundary geometry;
- ramp width configuration correction toward 4 m group target.

### Runtime status

Последний supplied Blender 5.2 runtime:

- terrain slope audit = **PASS (19.88° max)**;
- capture overlays = **10 objects / 5 logical anchors**;
- Crown visual correction = **executed**;
- capture route binding = **PASS, 18 links**;
- ramps built = **5**;
- pockets reachable = **4/4**;
- gameplay symmetry = **PASS**;
- dedicated minion traversal = **PASS**;
- final Stage 9 validation = **FAILED**.

### Open gates

- свежий Blender runtime после последних validator/ramp changes;
- подтверждение 4 m ramp width;
- review Crown structural overlaps;
- resource generation remains **NOT IMPLEMENTED** in the active pipeline;
- final environment dressing remains open;
- no MAP LOCK.

### Hard constraints

- Base/Objective XY remain frozen;
- symmetry `(x,y,z) -> (-x,y,z)` remains mandatory;
- visual guides are navigation-neutral;
- outer boundary is validated by dedicated footprint rules;
- false-positive filtering is narrow and evidence-based;
- validation failure cannot be reclassified as release success.

---

# v0.6.5 — FULL DOMINION SIMULATION + MAP BALANCE

Полная детерминированная симуляция 5v5, баланс objectives, rotation, comeback, deathball, snowball и time-to-objective.

# v0.6.6 — FINAL VALIDATION + EXPORT + MAP LOCK

Финальная проверка Blender-карты и фиксация MAP LOCK перед UE5.

# v0.7.0 — UNREAL ENGINE 5 FOUNDATION

После MAP LOCK начинается интеграция игрового runtime в UE5.
