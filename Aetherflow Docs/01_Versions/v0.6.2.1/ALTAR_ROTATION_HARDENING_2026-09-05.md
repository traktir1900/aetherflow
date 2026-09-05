# v0.6.2.1 — Altar / Rotation Hardening

Дата: 2026-09-05  
Ветка: `v0-6-2-1-cover-refinement`

## Основание

Последний Blender 5.2 runtime report дал `89.8/100`.
Критических ошибок не было; navigation = `100`, pocket reachability = `4/4`, actual evaluated-mesh intersections = `0`.

Оставшиеся проблемы отчёта:

- `Altar` — `HIGH camping risk`;
- `AltarObstacles: 0` — отдельная категория отсутствовала;
- minimum vertex-to-surface distance до Altar = `6.458 m`, ниже целевого clearance `7.5 m`;
- rotation variance = `21.6 s`, при этом сам отчёт помечает эту метрику как approximation для Base→CapturePoint routes.

## Выполненные изменения

### 1. Altar clearance

Добавлен `core/altar_rotation.py`.

`ensure_altar_clearance()` анализирует реальные world-space vertices `Core_Cover_*` и радиально выдвигает меши наружу до target clearance `8.5 m`.
Проверка идемпотентна: повторный запуск не должен продолжать двигать уже исправленные объекты.

### 2. AltarObstacle category

Добавлены четыре объекта:

- `Altar_Obstacle_01`
- `Altar_Obstacle_02`
- `Altar_Obstacle_03`
- `Altar_Obstacle_04`

Тип: `altar_obstacle`.  
Они экспортируются в `props` и намеренно не участвуют в navigation blockers, чтобы не менять проверенную reachability.

### 3. Rotation metric

Добавлен `navigation.macro_rotation` в pipeline.
Метрика определяется как реальные nav-маршруты между соседними capture points пятиугольного кольца.

Это отделяет настоящую objective-to-objective macro rotation от простого разброса всех Base→Objective маршрутов.

## Что считать успешным runtime после изменений

1. `Altar_Obstacle_*` = `4`.
2. Minimum CoreCover→Altar clearance >= `8.0 m`.
3. Actual mesh intersections = `0`.
4. Navigation problems = `0`.
5. Pockets reachable = `4/4`.
6. `navigation.macro_rotation` присутствует и все 5 ring edges reachable.
7. Objective gameplay cover остаётся `10` / `5 objectives`.

## Статус

Код обновлён в ветке, но новый runtime Blender 5.2 ещё не выполнен после этого hardening pass.
Следовательно, новые значения выше являются целевыми инвариантами, а не подтверждёнными runtime-результатами.
