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

### Главная задача

Превратить существующий каркас v0.6.1 в полноценное игровое пространство, не меняя фундаментальную топологию карты.

В этой версии не создаются заново базы, точки, дороги, рампы, рельеф или pockets. Они уже существуют. Работа направлена на их игровое оформление, окружение, укрытия, точки взаимодействия и данные, необходимые для будущего UE5.

## v0.6.2.0 — BASELINE LOCK

Зафиксировать существующий фундамент:

- layout;
- 5 objectives;
- 2 bases;
- terrain;
- roads;
- ramps;
- pockets;
- boundary;
- navigation;
- текущую систему валидации.

Перед изменениями сохранить baseline метрики:

- размеры карты;
- позиции объектов;
- navigation coverage;
- travel distances;
- LOS;
- существующие gameplay cover;
- экспортируемые идентификаторы.

Новые декоративные системы не должны случайно менять этот фундамент.

## v0.6.2.1 — GAMEPLAY COVER 2.0

Расширить существующую систему укрытий, а не создавать вторую независимую систему.

Добавить контролируемые категории укрытий для:

- подходов к objectives;
- отходов;
- флангов;
- ротаций;
- pockets;
- defensive positions;
- атакующих позиций;
- choke points.

Использовать существующий cover optimizer и его ограничения.

Базовые ограничения:

- максимум 3 объекта укрытия в pocket;
- максимум 15% покрытия пола pocket;
- минимум 3 м свободного прохода;
- контроль влияния укрытий на navigation и LOS.

## v0.6.2.2 — EXPANDED ROCK SYSTEM

Расширить существующий `core/rocks.py`.

Не заменять текущую генерацию камней.

Добавить логические категории:

- gameplay rocks;
- decorative rocks;
- large rocks;
- rock groups;
- tactical formations;
- perimeter rocks.

Для каждой категории определить:

- размер;
- footprint;
- variation;
- rotation;
- seed;
- collision/navigation behaviour;
- gameplay/decorative статус.

Камни должны оставаться детерминированными и не создавать случайные непроходимые зоны.

## v0.6.2.3 — NATURAL ENVIRONMENT INTEGRATION

Интегрировать существующий `geometry/natural_perimeter.py` в основной pipeline.

Использовать уже предусмотренные linked assets:

- cliffs / boulders;
- rocks;
- trees;
- shrubs;
- grass;
- hanging grass;
- plants groups.

Главная задача — сделать систему частью реальной генерации карты, а не отдельным неиспользуемым модулем.

## v0.6.2.4 — ENVIRONMENT DISTRIBUTION

Создать gameplay-aware распределение окружения.

Разные плотности для:

- внешнего периметра;
- основных ротаций;
- второстепенных маршрутов;
- objectives;
- центральной боевой зоны;
- pockets;
- баз;
- spawn areas.

Избегать равномерного случайного scatter по всей карте.

## v0.6.2.5 — GAMEPLAY-AWARE VEGETATION

Растительность должна учитывать:

- terrain;
- objectives;
- bases;
- roads;
- ramps;
- pockets;
- combat areas;
- navigation;
- boundary.

Декоративная растительность не должна:

- блокировать navigation;
- создавать искусственное укрытие;
- перекрывать capture zones;
- закрывать дороги;
- мешать minion routes;
- создавать бесплатные backdoor-позиции.

## v0.6.2.6 — OBJECTIVE DRESSING

Оформить существующие пять objectives:

- Crown;
- EastMonolith;
- SEMonolith;
- SWMonolith;
- WestMonolith.

Для каждого определить и экспортировать:

- визуальный центр;
- capture area;
- interaction point;
- UI anchor;
- tactical cover;
- defensive area;
- attacking area;
- окружающее оформление.

Визуальная форма объекта может различаться, но gameplay footprint должен оставаться контролируемым.

## v0.6.2.7 — CAPTURE INTERACTION FOUNDATION

Для каждого objective создать Blender-side данные/маркеры:

- `CaptureZone`;
- `CaptureCenter`;
- `InteractionPoint`;
- `UIAnchor`;
- стабильный objective ID;
- team ownership data placeholder;
- capture radius;
- contest radius.

Это фундамент будущей механики UE5. Реальная логика захвата и UI реализуются после перехода в UE5.

## v0.6.2.8 — CAPTURE UI SPECIFICATION

Подготовить данные для будущего интерфейса.

Определить:

- состояние objective;
- текущего владельца;
- contested state;
- capture progress;
- neutral state;
- direction of capture;
- world-space UI anchor.

Будущий UI должен поддерживать двунаправленную шкалу захвата и состояние `[CAPTURE]` для взаимодействия.

Blender экспортирует данные и маркеры. Widget создаётся в UE5.

## v0.6.2.9 — BASE SHOP FOUNDATION

Добавить к существующим базам:

- `Shop_Blue`;
- `Shop_Red`;
- interaction marker;
- UI anchor;
- стабильный ID.

Не реализовывать экономику, покупки или inventory.

Это только пространственный и экспортный фундамент будущего магазина.

## v0.6.2.10 — BASE DRESSING

Легко оформить Blue Base и Red Base:

- spawn area;
- protected area;
- shop area;
- визуальные элементы;
- defensive dressing;
- вход/выход;
- локальное окружение.

Не менять положение и основной gameplay footprint баз.

## v0.6.2.11 — UNIFIED GAMEPLAY MARKERS

Создать единую систему маркеров для будущего UE5.

Поддержать:

- objectives;
- bases;
- shops;
- AetherCore;
- future pickups;
- spawn points;
- capture interaction;
- UI anchors.

Все маркеры должны иметь стабильные IDs и экспортироваться через единый формат.

## v0.6.2.12 — AETHERCORE DRESSING

Оформить существующий AetherCore как центральный gameplay landmark.

Добавить:

- визуальный центр;
- окружение;
- декоративные formations;
- контролируемые tactical cover elements;
- interaction/data marker при необходимости.

**AetherCore не становится шестой capture point.**

## v0.6.2.13 — ENVIRONMENT SAFETY

После размещения окружения сравнить baseline и новую сцену.

Проверить:

- navigation;
- проходы;
- roads;
- ramps;
- capture zones;
- base zones;
- minion corridors;
- LOS;
- cover;
- collision.

Декоративные объекты по умолчанию не должны блокировать gameplay navigation.

## v0.6.2.14 — VISUAL VALIDATION

Проверить отсутствие:

- пустых gameplay-зон;
- чрезмерно плотных участков;
- визуального шума;
- повторяющихся паттернов;
- floating assets;
- пересечений;
- объектов внутри дорог;
- объектов внутри capture zones;
- случайных wall-like formations.

## v0.6.2.15 — DETERMINISTIC ENVIRONMENT

Гарантировать:

- одинаковый seed → одинаковая карта;
- другой seed → другое окружение;
- layout objectives/bases не меняется от decorative seed;
- gameplay geometry остаётся контролируемой.

Разделить gameplay seed и environment seed, если это необходимо архитектурно.

## v0.6.2.16 — EXPORT EXTENSION

Расширить `map_data.json`.

Добавить данные:

- objectives;
- bases;
- shops;
- capture zones;
- interaction points;
- UI anchors;
- gameplay cover;
- environment instances;
- gameplay markers.

Сохранить совместимость с уже существующим экспортом.

## v0.6.2.17 — FINAL VALIDATION

Проверить:

- pipeline generation;
- deterministic generation;
- geometry integrity;
- navigation;
- LOS;
- cover;
- environment safety;
- objective data;
- base/shop markers;
- capture interaction data;
- export;
- validation scripts.

Результат: карта получает полноценный gameplay dressing и foundation для UE5, при этом существующий фундамент v0.6.1 остаётся стабильным.

---

# v0.6.3 — TERRAIN + ROADS + RAMPS + POCKETS + COMBAT SPACE REFINEMENT

### Главная задача

Доработать физическое игровое пространство только там, где реальные тесты v0.6.2 показывают проблемы.

Это не обязательная перестройка карты. Все изменения должны быть evidence-driven.

## v0.6.3.1 — TERRAIN REFINEMENT

Проверить и при необходимости улучшить:

- AetherCore depression;
- Crown elevation;
- central plateau;
- WestMonolith elevation;
- EastMonolith elevation;
- South Rift;
- lowlands;
- transitions.

## v0.6.3.2 — HEIGHT TRANSITIONS

Проверить:

- slope;
- ramps;
- walkability;
- minion traversal;
- LOS changes;
- combat readability.

Исправлять только реальные проблемы.

## v0.6.3.3 — ROAD NETWORK REFINEMENT

Проверить:

- base → objective;
- objective → objective;
- outer rotation;
- inner rotation;
- flank routes;
- pocket routes;
- retreat routes.

Не создавать классические три MOBA lanes.

## v0.6.3.4 — RAMP REFINEMENT

Проверить существующие рампы для:

- героя;
- minion;
- группы;
- 5 игроков.

Исправить только узкие, слишком крутые или плохо читаемые переходы.

## v0.6.3.5 — POCKET REFINEMENT

Проверить существующие:

- WestPocket;
- EastPocket;
- SWPocket;
- SEPocket.

Сохранить их назначение как flank / ambush / retreat spaces.

## v0.6.3.6 — COMBAT COVER REFINEMENT

Использовать существующий cover optimizer для проблемных зон.

Не допускать чрезмерного заполнения карты укрытиями.

## v0.6.3.7 — COMBAT SPACE TESTING

Проверить реальные сценарии:

- 1v1;
- 2v2;
- 3v3;
- 5v5;
- retreat;
- flank;
- interception;
- objective defense;
- objective assault.

## v0.6.3.8 — DEATHBALL MITIGATION

Если тесты показывают чрезмерное преимущество deathball, использовать:

- дополнительные входы;
- flank routes;
- split routes;
- interception paths;
- LOS breaks;
- controlled choke points.

Не решать проблему простым добавлением большого количества препятствий.

## v0.6.3.9 — MAP READABILITY

Проверить, что игрок может быстро определить:

- где находится objective;
- куда ведёт основной маршрут;
- где возможен flank;
- где безопасный retreat;
- где опасная зона.

## v0.6.3.10 — VERSION VALIDATION

Зафиксировать результаты тестов и определить, готова ли карта перейти к полной simulation/balance фазе.

---

# v0.6.4 — BOUNDARY + ENVIRONMENT + RESOURCES COMPLETION

### Главная задача

Завершить физическую и визуальную оболочку карты и добавить ресурсные точки, необходимые для Dominion-подобной ротации.

## v0.6.4.1 — OUTER BOUNDARY

Финализировать:

- cliffs;
- walls;
- boulders;
- natural formations;
- collision;
- visual boundary;
- camera readability.

Проверить реальную игровую границу отдельно от декоративного perimeter.

## v0.6.4.2 — NATURAL PERIMETER COMPLETION

Довести интеграцию natural perimeter до production-ready состояния:

- cliffs;
- rocks;
- trees;
- shrubs;
- grass;
- plants.

Исключить дублирование `OuterBoundary` и повторную генерацию уже зарегистрированных collections.

## v0.6.4.3 — ENVIRONMENT POLISH

Настроить распределение окружения по gameplay-зонам.

Проверить:

- плотность;
- вариативность;
- repetition;
- asset intersections;
- visual hierarchy.

## v0.6.4.4 — HEALTH RELICS

Подготовить точки восстановления здоровья.

Для каждой точки определить:

- marker;
- position;
- radius;
- respawn placeholder;
- UI/data ID.

Не реализовывать UE5 gameplay.

## v0.6.4.5 — SPEED SHRINES

Подготовить точки ускорения:

- marker;
- radius;
- direction/route context;
- UI/data ID.

Использовать существующие конфигурационные параметры `speed_shrine_radius` и `shrine_road_offset`.

## v0.6.4.6 — RESOURCE DISTRIBUTION

Расположить ресурсы так, чтобы они:

- стимулировали rotation;
- создавали риск/награду;
- не блокировали roads;
- не давали одной базе систематического преимущества;
- были доступны несколькими маршрутами.

## v0.6.4.7 — RESOURCE FAIRNESS

Сравнить Blue/Red:

- travel time;
- distance to resource;
- risk;
- alternative approaches;
- retreat options.

## v0.6.4.8 — FINAL ENVIRONMENT VALIDATION

Проверить всю внешнюю оболочку, environment и resources вместе с navigation и gameplay geometry.

---

# v0.6.5 — FULL DOMINION SIMULATION + MAP BALANCE

### Главная задача

Перейти от технической simulation к реальной модели Dominion-подобного матча.

## v0.6.5.1 — OBJECTIVE OWNERSHIP

Реализовать:

- Neutral;
- Blue;
- Red;
- contested;
- capture progress;
- neutralization.

Убрать искусственную модель вида `idx % 2`.

## v0.6.5.2 — CAPTURE / NEUTRALIZATION

Моделировать:

- захват нейтральной точки;
- нейтрализацию вражеской точки;
- contested state;
- скорость захвата;
- влияние нескольких игроков.

## v0.6.5.3 — TICKET / SCORE MODEL

Создать модель преимущества по контролю objectives.

Проверить:

- преимущество по количеству точек;
- скорость потери ресурса/тикетов;
- comeback potential;
- snowball.

## v0.6.5.4 — OBJECTIVE PRESSURE

Добавить симуляцию давления от контролируемых точек:

- destination;
- соседняя точка;
- маршрут;
- minion pressure;
- состояние objective.

Миньоны должны иметь конкретную цель, а не двигаться бесконечно по карте.

## v0.6.5.5 — ROTATION SIMULATION

Симулировать:

- base → objective;
- objective → objective;
- outer rotation;
- inner rotation;
- flank;
- retreat;
- interception.

## v0.6.5.6 — 5v5 SCENARIOS

Запустить набор deterministic сценариев:

- равный старт;
- ранний захват;
- потеря центра;
- split push;
- deathball;
- backdoor;
- comeback;
- две контролируемые точки;
- три контролируемые точки;
- длительный contested fight.

## v0.6.5.7 — MAP BALANCE METRICS

Собирать:

- travel time;
- objective access;
- capture exposure;
- LOS;
- cover advantage;
- flank availability;
- retreat distance;
- resource access.

## v0.6.5.8 — BALANCE ITERATION

Исправлять только доказанные дисбалансы.

Приоритет:

1. unfair travel;
2. unfair objective access;
3. impossible defense;
4. excessive deathball;
5. excessive backdoor;
6. resource imbalance.

---

# v0.6.6 — FINAL VALIDATION + EXPORT + MAP LOCK

### Главная задача

Заморозить Blender/Python карту перед переходом в UE5.

## v0.6.6.1 — FULL GENERATION TEST

Проверить чистую генерацию с нуля.

## v0.6.6.2 — DETERMINISM TEST

Проверить одинаковый seed и сравнить:

- geometry;
- object IDs;
- environment;
- navigation;
- export.

## v0.6.6.3 — GAMEPLAY VALIDATION

Проверить:

- 5 objectives;
- 2 bases;
- routes;
- pockets;
- resources;
- cover;
- LOS;
- navigation;
- simulation.

## v0.6.6.4 — EXPORT VALIDATION

Проверить `map_data.json` и все обязательные IDs/markers.

## v0.6.6.5 — MAP LOCK

После прохождения validation:

- зафиксировать layout;
- зафиксировать objective positions;
- зафиксировать base positions;
- зафиксировать roads/ramp topology;
- зафиксировать gameplay geometry;
- создать release baseline для UE5.

**v0.6.6 = последний этап изменения игровой карты в Blender/Python перед UE5.**

---

# ФАЗА 2 — UNREAL ENGINE 5

# v0.7.0 — UE5 FOUNDATION

### Главная задача

Импортировать и собрать зафиксированную карту в Unreal Engine 5.8 без изменения gameplay topology.

## v0.7.0.1 — UE5 PROJECT FOUNDATION

- UE5 project structure;
- source control integration;
- C++ foundation;
- gameplay modules;
- naming conventions;
- folder structure.

## v0.7.0.2 — MAP IMPORT

Импортировать:

- terrain;
- structures;
- roads;
- ramps;
- rocks;
- environment;
- boundary.

## v0.7.0.3 — COLLISION + NAVIGATION

Проверить:

- collision;
- NavMesh;
- walkability;
- ramps;
- minion paths;
- boundary.

## v0.7.0.4 — MAP DATA IMPORT

Импортировать `map_data.json` и связать:

- objectives;
- bases;
- shops;
- capture zones;
- markers;
- resources;
- UI anchors.

## v0.7.0.5 — UE5 MAP VALIDATION

Сравнить Blender baseline и UE5:

- positions;
- dimensions;
- IDs;
- navigation;
- collision;
- gameplay zones.

---

# ФАЗА 3 — DOMINION GAMEPLAY

## v0.8.x — DOMINION GAMEPLAY CORE

- objective actors;
- capture/neutralization;
- ownership;
- contested state;
- ticket/score system;
- objective pressure;
- match state;
- win/lose conditions.

## v0.9.x — PLAYER

- player controller;
- movement;
- camera;
- spawn;
- respawn;
- basic interaction;
- capture interaction.

## v0.10.x — COMBAT

- health;
- damage;
- death;
- basic attacks;
- targeting;
- combat feedback.

## v0.11.x — ABILITY FRAMEWORK

- ability system;
- cooldowns;
- resources;
- targeting;
- effects;
- status effects.

## v0.12.x — HERO #1

Первый полноценный игровой герой.

## v0.13.x — MINIONS

- minion spawning;
- objective pressure;
- paths;
- combat;
- targeting;
- death/reward.

## v0.14.x — ECONOMY

- gold;
- rewards;
- kill rewards;
- objective rewards;
- match economy.

## v0.15.x — ITEMS

- shop;
- item definitions;
- purchases;
- inventory;
- stats;
- item effects.

## v0.16.x — TEAM SYSTEM

- teams;
- allies/enemies;
- team spawn;
- team score;
- team state.

## v0.17.x — COMPLETE 5v5

- 5 players per team;
- full objective gameplay;
- minions;
- economy;
- combat;
- respawn;
- victory conditions.

---

# ФАЗА 4 — GAME MODES

## v0.18.x — STATIC MODE

Основной стабильный режим AetherFlow.

## v0.19.x — HYBRID MODE

Комбинация фиксированных и динамических objectives/rules.

## v0.20.x — DYNAMIC MODE

Динамическое изменение состояния карты и objectives.

---

# ФАЗА 5 — MULTIPLAYER

## v0.21.x — MULTIPLAYER FOUNDATION

- replication;
- server authority;
- networked gameplay;
- player state;
- team state.

## v0.22.x — ONLINE MATCH

- lobby;
- matchmaking foundation;
- session;
- connect/disconnect;
- full online match flow.

---

# ФАЗА 6 — UI / GAME FEEL / CONTENT

## v0.23.x — UI

- HUD;
- objective UI;
- capture bar;
- minimap;
- scoreboard;
- shop UI;
- match state.

## v0.24.x — GAME FEEL

- VFX;
- SFX;
- hit feedback;
- capture feedback;
- movement feedback;
- camera polish.

## v0.25.x — HERO ROSTER

Расширение состава героев.

## v0.26.x — CONTENT

- additional maps/content;
- objectives;
- environments;
- effects;
- audio;
- cosmetics where applicable.

---

# ФАЗА 7 — BALANCE / QA / RELEASE

## v0.27.x — BALANCE

- heroes;
- items;
- economy;
- objectives;
- minions;
- game modes.

## v0.28.x — QA

- functional testing;
- regression testing;
- multiplayer testing;
- exploit testing;
- edge cases.

## v0.29.x — PERFORMANCE

- CPU;
- GPU;
- memory;
- network;
- loading;
- scalability.

## v0.30+ — ALPHA

Полный playable build.

## v0.40+ — BETA

Feature-complete build с фокусом на баланс и стабильность.

## v0.90+ — RELEASE CANDIDATE

Финальная подготовка релиза.

## v1.0.0 — RELEASE

Первый официальный релиз AetherFlow.

---

# КЛЮЧЕВОЙ ПРИНЦИП ROADMAP

**0.6.x = Blender / Python / карта.**

**0.6.1 = существующий фундамент.**

**0.6.2 = gameplay dressing, environment и interaction foundation.**

**0.6.3 = refinement только по результатам тестов.**

**0.6.4 = boundary, environment и resources completion.**

**0.6.5 = полноценная Dominion simulation и balance.**

**0.6.6 = validation, export и MAP LOCK.**

**0.7.0 = переход в Unreal Engine 5.**

После MAP LOCK изменение фундаментальной топологии карты не должно происходить в рамках обычной разработки. Изменения карты после этого момента должны проходить как отдельные контролируемые map revisions.
