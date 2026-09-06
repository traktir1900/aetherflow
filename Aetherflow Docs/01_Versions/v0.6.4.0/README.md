# AetherFlow v0.6.4.0 — Boundary, Environment & Runtime Presentation

Статус: IN PROGRESS. Реализация присутствует; для финального закрытия версии требуется свежий runtime-тест в Blender 5.2.

Эта версия охватывает boundary/environment pass и связанные gameplay-presentation corrections поверх стабильного фундамента v0.6.3.2.

Текущий контракт:
- gameplay area: 200 × 200 м;
- world floor: 220 × 220 м;
- objectives: 5/5;
- bases: 2;
- gameplay pockets: 4;
- outer boundary: elliptical, 48 segments;
- symmetry: `(x,y,z) -> (-x,y,z)`;
- tolerance: 0.25 м;
- deterministic seed: 1337.

## Реализовано

1. Global outer elliptical boundary с отдельной validation-моделью.
2. Intentional Crown outer-wall opening.
3. Crown Sanctum presentation и raised-objective visibility.
4. Отдельный capture stack для всех пяти objectives.
5. Visual-only road light guides.
6. Capture route binding.
7. Runtime compatibility для visual-only и boundary-specific geometry.
8. Исправление ширины ramps к 4 м group-width contract.
9. Основа для будущих resources/environment systems.

## Критическое разделение Crown

`CapturePlatform_Crown`, `CaptureIndicatorRing_Crown` и `CaptureButton_Crown` — отдельные сущности capture system.

`Crown_BossButton` — отдельная boss interaction сущность и не может использоваться как capture platform, capture control или navigation node.

## Runtime status

Последний предоставленный runtime показал PASS по terrain slope, 5/5 objectives, 4/4 pockets, symmetry, minion traversal и capture routing; общий Stage 9 validation оставался FAILED.

Следующая точка закрытия — свежий Blender 5.2 runtime с нулём genuine validation errors.

## Следующая версия

После закрытия v0.6.4.0: `v0.6.5` — FULL DOMINION SIMULATION + MAP BALANCE.
