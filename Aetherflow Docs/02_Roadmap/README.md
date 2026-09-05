# AetherFlow — Полный план разработки

## Этап Blender / Python / игровая карта

---

# ФАЗА 1 — BLENDER / PYTHON / ИГРОВАЯ КАРТА

## v0.6.1 — ТЕКУЩАЯ БАЗОВАЯ ВЕРСИЯ

Текущая рабочая версия карты.

Уже существует:

- процедурная генерация карты
- процедурный рельеф
- heightmap
- 5 точек захвата
- 2 базы
- дороги
- рампы
- камни
- игровые карманы
- система укрытий
- анализ прямой видимости
- навигационная система
- внешняя граница карты
- симуляция
- валидация
- экспорт

Размер игровой области сейчас: **200 × 200 м**.

Размер внешнего пола: **220 × 220 м**.

v0.6.1 является исходной точкой для дальнейшей разработки.

---

# v0.6.2 — БАЗЫ + ТОЧКИ ЗАХВАТА + ТОПОГРАФИЯ КАРТЫ

### Главная задача

Полностью сформировать игровую структуру карты вокруг:

- 5 точек захвата
- 2 баз
- маршрутов между точками
- ротации
- обходов
- флангов
- атакующих и защитных направлений

Отдельного этапа аудита нет.

## v0.6.2.1 — ПЯТЬ ТОЧЕК ЗАХВАТА

Финализировать:

- Crown
- EastMonolith
- SEMonolith
- SWMonolith
- WestMonolith

Каждая точка должна иметь:

- платформу захвата
- радиус захвата
- зону оспаривания
- центр объекта
- основную конструкцию
- оборонительную конструкцию
- атакующую зону
- оборонительную зону
- зону отхода
- укрытия
- зоны прямой видимости
- фланговые подходы
- пути отхода

## v0.6.2.2 — ДИЗАЙН ТОЧЕК ЗАХВАТА

Точка не должна быть просто круглой платформой.

Вокруг неё формируется полноценная боевая зона:

- основной подход
- второй подход
- фланговый подход
- тыловой подход
- оборонительная позиция
- позиция атакующих
- позиция отхода
- маршрут контратаки

Каждая точка должна иметь минимум два полноценных направления атаки.

## v0.6.2.3 — ОБОРОНА ТОЧЕК

Для каждой точки:

- оборонительная конструкция
- сектор атаки
- слепые зоны
- защитные укрытия
- укрытия атакующих
- возможность нейтрализации

Принцип Dominion:

**Точка захвата = объект захвата + ограниченная оборона.**

Это не обычная MOBA-башня.

## v0.6.2.4 — СИНЯЯ БАЗА

Полностью разработать Blue Base:

- площадка возрождения
- зона появления
- защищённая зона
- магазин
- основная дорога выхода
- дополнительный выход
- оборонительная зона
- путь отхода
- соединения с ближайшими точками

## v0.6.2.5 — КРАСНАЯ БАЗА

Разработать Red Base:

- площадка возрождения
- зона появления
- защищённая зона
- магазин
- основной выход
- дополнительный выход
- оборонительная зона
- путь отхода
- соединения с ближайшими точками

Игровая геометрия должна быть сбалансирована относительно Blue Base. Визуально базы могут различаться.

## v0.6.2.6 — СВЯЗЬ БАЗ С ТОЧКАМИ

Определить:

- ближайшие точки
- стартовые маршруты
- атакующие маршруты
- защитные маршруты
- маршруты ротации
- пути контратаки

Базы должны естественно включаться в систему ротации.

## v0.6.2.7 — ТОПОГРАФИЯ DOMINION

Создать окончательный граф пяти точек:

- соседние точки
- дополнительные связи
- внутренние маршруты
- внешние маршруты
- связи с базами

Не использовать классическую структуру верхняя / центральная / нижняя линия.

Основная логика:

**ТОЧКА → ТОЧКА → ТОЧКА**

## v0.6.2.8 — ВНЕШНЯЯ РОТАЦИЯ

Создать основной маршрут вокруг карты:

- быстрая ротация
- понятное перемещение
- преследование
- отход
- перехват

Это основной безопасный маршрут.

## v0.6.2.9 — ВНУТРЕННЯЯ РОТАЦИЯ

Создать внутренние сокращённые маршруты.

Они должны быть:

- быстрее
- опаснее
- менее предсказуемыми
- пригодными для засад
- пригодными для перехвата

## v0.6.2.10 — ФЛАНГИ И BACKDOOR

Создать:

- левый фланг
- правый фланг
- тыловой подход
- обход точки
- обход обороны
- backdoor-маршрут

Backdoor должен быть возможен, но требовать времени, риска, отсутствия защитника и правильной информации.

## v0.6.2.11 — БАЛАНС РОТАЦИИ

Рассчитать:

- база → точка
- точка → соседняя точка
- точка → точка
- внешний маршрут
- внутренний маршрут

Сравнить Blue и Red.

## v0.6.2.12 — СПРАВЕДЛИВОСТЬ ТОЧЕК

Для каждой точки определить:

- время подхода
- количество входов
- количество выходов
- количество укрытий
- прямую видимость
- возможность фланга
- преимущество защиты
- преимущество атаки

---

# v0.6.3 — РЕЛЬЕФ + ДОРОГИ + РАМПЫ + КАРМАНЫ + БОЕВЫЕ ЗОНЫ

### Главная задача

Превратить топологию в полноценное игровое пространство.

## v0.6.3.1 — ОСНОВНОЙ РЕЛЬЕФ

Доработать:

- впадину AetherCore
- возвышенность Crown
- центральное плато
- возвышенность WestMonolith
- возвышенность EastMonolith
- South Rift
- низины
- переходы между уровнями

## v0.6.3.2 — ПЕРЕХОДЫ РЕЛЬЕФА

Все перепады высот должны быть:

- плавными
- читаемыми
- проходимыми
- пригодными для боя
- пригодными для миньонов

Проверить:

- уклоны
- рампы
- возвышенности
- низины
- разрывы прямой видимости

## v0.6.3.3 — СЕТЬ ДОРОГ

### Основные дороги

- база → точка
- точка → точка

### Второстепенные дороги

- фланги
- карманы
- короткие пути

### Тактические маршруты

- засады
- перехваты
- отход
- backdoor

## v0.6.3.4 — РАМПЫ

Доработать:

- входы на центральное плато
- рампы точек
- входы в карманы
- переходы возле баз

Проверить ширину для:

- героя
- миньона
- группы
- команды 5 игроков

## v0.6.3.5 — ИГРОВЫЕ КАРМАНЫ

Доработать существующие:

- WestPocket
- EastPocket
- SWPocket
- SEPocket

Каждый должен иметь:

- вход
- выход
- укрытие
- фланг
- засаду
- путь отхода
- связь с точкой

## v0.6.3.6 — УКРЫТИЯ В КАРМАНАХ

Использовать существующий оптимизатор укрытий.

Ограничения:

- максимум 3 объекта укрытия
- максимум 15% площади пола
- минимум 3 м свободного прохода

## v0.6.3.7 — БОЕВЫЕ ЗОНЫ

Создать:

- зоны боя возле точек
- открытые боевые зоны
- зоны боя в карманах
- зоны боёв при ротации
- оборонительные зоны
- зоны засад

## v0.6.3.8 — СИСТЕМА УКРЫТИЙ

Настроить:

- полные укрытия
- частичные укрытия
- боковые укрытия
- укрытия точки
- укрытия для отхода

## v0.6.3.9 — ПРЯМАЯ ВИДИМОСТЬ

Проверить:

- видимость героя
- видимость точки
- видимость оборонительной конструкции
- видимость миньонов
- слепые зоны

## v0.6.3.10 — УЗКИЕ МЕСТА

Для каждого choke point определить:

- ширину
- длину
- укрытия
- прямую видимость
- выходы
- альтернативный маршрут

## v0.6.3.11 — ГЕОМЕТРИЯ ПРОТИВ DEATHBALL

Создать:

- маршруты разделения
- несколько входов
- перекрёстный огонь
- фланговые маршруты
- альтернативные точки
- маршруты перехвата

Цель: **5 игроков вместе сильны, но не должны автоматически контролировать всю карту.**

---

# v0.6.4 — ГРАНИЦА + ОКРУЖЕНИЕ + РЕСУРСЫ DOMINION

### Главная задача

Закончить физическую и визуальную оболочку карты и добавить элементы, заставляющие игроков перемещаться.

## v0.6.4.1 — ВНЕШНЯЯ ГРАНИЦА

Доработать:

- скалы
- стены
- камни
- естественные образования
- collision
- визуальную границу

Проверить:

- толщину
- высоту
- читаемость
- камеру
- реальные игровые границы

## v0.6.4.2 — ЕСТЕСТВЕННЫЙ ПЕРИМЕТР

Полностью интегрировать:

- скалы
- камни
- деревья
- кусты
- траву
- растения

Проверить интеграцию существующего `natural_perimeter.py` в основной pipeline.

## v0.6.4.3 — РАСПРЕДЕЛЕНИЕ ОКРУЖЕНИЯ

Процедурно разместить:

- камни
- деревья
- кусты
- растительность
- руины
- декоративные объекты

Распределение должно учитывать gameplay.

## v0.6.4.4 — БЕЗОПАСНОСТЬ ОКРУЖЕНИЯ

Окружение не должно случайно:

- перекрывать дороги
- блокировать точки
- блокировать базы
- создавать лишние укрытия
- блокировать навигацию
- блокировать миньонов
- создавать бесплатный backdoor

## v0.6.4.5 — РЕЛИКВИИ ЗДОРОВЬЯ

Создать места для:

- восстановления здоровья
- фиксированного расположения
- контролируемого respawn
- риска при подборе

Расположение должно стимулировать ротацию.

## v0.6.4.6 — SPEED SHRINES

Создать:

- зоны ускорения
- ускорение ротации
- возможности отхода
- возможности перехвата

Обычные дороги всё равно должны оставаться полезными.

## v0.6.4.7 — ЦЕНТРАЛЬНЫЙ РЕСУРС

Разработать AetherCore как центральный ресурсный объект.

Принцип:

**ВЫСОКИЙ РИСК → ВРЕМЕННОЕ ПРЕИМУЩЕСТВО**

Центр должен периодически заставлять команды бороться за него.

## v0.6.4.8 — БАЛАНС РЕСУРСОВ

Проверить:

- доступность
- время подхода
- риск
- награду
- время respawn
- влияние на ротацию

---

# v0.6.5 — ПОЛНАЯ СИМУЛЯЦИЯ DOMINION + БАЛАНС КАРТЫ

### Главная задача

Проверить не только техническую корректность карты, а то, интересно ли на ней реально играть.

## v0.6.5.1 — СОСТОЯНИЯ ТОЧЕК

Симулировать:

- Neutral
- Blue
- Red
- захват
- нейтрализацию
- contest
- прерывание захвата
- постепенный возврат точки

## v0.6.5.2 — ДАВЛЕНИЕ СОСЕДНИХ ТОЧЕК

Создать модель:

**ЗАХВАЧЕННАЯ ТОЧКА → ДАВЛЕНИЕ → СОСЕДНЯЯ ВРАЖЕСКАЯ ТОЧКА**

Это фундамент будущей системы миньонов.

## v0.6.5.3 — МАРШРУТИЗАЦИЯ МИНЬОНОВ

Логика:

**Spawn → Target Objective**

а не просто движение по карте.

Для каждой точки определить:

- соседнюю точку
- целевую точку
- маршрут
- время движения

## v0.6.5.4 — СИМУЛЯЦИЯ 1v1

Проверить:

- перемещение
- захват
- защиту
- ротацию
- фланг
- отход

## v0.6.5.5 — СИМУЛЯЦИЯ 2v2

Проверить:

- давление на точку
- ротацию
- разделение
- бой

## v0.6.5.6 — СИМУЛЯЦИЯ 3v3

Проверить:

- обмен точками
- разделение
- ротацию
- командный бой

## v0.6.5.7 — СИМУЛЯЦИЯ 4v4

Проверить:

- deathball
- split
- фланги
- обмен точками

## v0.6.5.8 — СИМУЛЯЦИЯ 5v5

Основной тест карты:

- командный бой
- контроль точек
- ротация
- разделение
- backdoor
- deathball
- comeback

## v0.6.5.9 — ТЕСТ DEATHBALL

Сценарии:

- 5v5 на одной точке
- 5v5 ротация
- 5v5 преследование
- 5v5 оборона

Проверить, не становится ли deathball оптимальной стратегией.

## v0.6.5.10 — ТЕСТ SPLIT

Сценарии:

- 4 + 1
- 3 + 2
- 2 + 2 + 1

Проверить:

- обмен точками
- давление
- принуждение к ротации
- атаку слабого направления

## v0.6.5.11 — ТЕСТ BACKDOOR

Проверить:

- незащищённую точку
- скрытый захват
- быстрый захват
- время реакции
- возможность защиты

## v0.6.5.12 — ТЕСТ SNOWBALL

Сценарий:

**3 точки → 4 точки → 5 точек**

Проверить:

- скорость усиления лидера
- возможность камбэка
- момент, когда победа становится неизбежной

## v0.6.5.13 — ТЕСТ COMEBACK

Проигрывающая команда должна иметь возможность:

- разделиться
- обменять objectives
- сделать backdoor
- перехватить ротацию
- contest
- вернуть контроль карты

## v0.6.5.14 — ТЕСТ КОНТРОЛЯ КАРТЫ

Проверить динамику:

**3–2 → 2–3 → 3–2 → 2–3**

Контроль карты должен регулярно меняться.

## v0.6.5.15 — ТЕМП МАТЧА

Измерять:

- первый контакт
- первый захват
- первую ротацию
- среднее время contest
- среднее время ротации
- среднее время боя
- частоту изменения контроля карты

## v0.6.5.16 — ИТОГОВЫЙ ОТЧЁТ

Сформировать:

- время перемещения
- доступность objectives
- использование маршрутов
- плотность укрытий
- плотность LOS
- плотность choke points
- риск deathball
- риск snowball
- потенциал comeback
- риск backdoor
- влияние ресурсов

---

# v0.6.6 — ФИНАЛЬНЫЙ BLENDER MAP LOCK

Это финальная техническая версия Blender/Python карты.

## v0.6.6.1 — ЧИСТАЯ ГЕНЕРАЦИЯ

Полный запуск:

**RESET → GENERATE → VALIDATE → EXPORT**

Без ручного исправления.

## v0.6.6.2 — ПРОВЕРКА ГЕОМЕТРИИ

Проверить:

- terrain
- objectives
- bases
- roads
- ramps
- rocks
- pockets
- boundary
- environment

## v0.6.6.3 — ПРОВЕРКА НАВИГАЦИИ

Проверить:

- Base → Objective
- Objective → Objective
- Pocket → Objective
- Pocket → Base
- Minion routes

## v0.6.6.4 — ПРОВЕРКА БОЕВЫХ ЗОН

Проверить:

- LOS
- cover
- choke
- flank
- escape
- objective combat

## v0.6.6.5 — ПРОВЕРКА DOMINION-ЛОГИКИ КАРТЫ

Проверить:

- 5 objectives
- 2 bases
- topology
- rotation
- capture geometry
- neighboring pressure
- backdoor
- split
- deathball
- comeback

## v0.6.6.6 — ДЕТЕРМИНИРОВАННОСТЬ

Одинаковый seed должен создавать **абсолютно одинаковую карту**.

## v0.6.6.7 — БЕЗОПАСНЫЙ ПОВТОРНЫЙ ЗАПУСК

Повторный запуск pipeline не должен создавать:

- дубликаты
- повторные objectives
- повторные bases
- повторные boundary
- повторные rocks
- повторную растительность

## v0.6.6.8 — ПРОИЗВОДИТЕЛЬНОСТЬ BLENDER

Проверить:

- количество объектов
- количество полигонов
- время генерации
- время генерации navigation
- время simulation
- использование памяти Blender

## v0.6.6.9 — ЭКСПОРТ В UE5

Подготовить:

- terrain
- objectives
- bases
- roads
- ramps
- rocks
- pockets
- boundary
- environment
- gameplay metadata

## v0.6.6.10 — ДОКУМЕНТАЦИЯ

Обновить:

- Map README
- Gameplay README
- Technical README
- GDD
- Versions
- Decisions
- Releases

## v0.6.6.11 — ФИНАЛЬНАЯ ВИЗУАЛЬНАЯ ПРОВЕРКА

Проверить карту:

- сверху
- с камеры игрока
- возле objectives
- возле баз
- внутри pockets
- в боевых зонах
- на границе карты

## v0.6.6.12 — MAP FOUNDATION LOCK

# BLENDER MAP LOCKED

После этой версии:

- крупная переработка карты запрещена
- новые системы карты не добавляются
- допускаются только bug fixes
- допускаются критические gameplay fixes
- крупные изменения выполняются отдельным change request

---

# ИТОГОВАЯ СТРУКТУРА BLENDER

| Версия | Основная работа |
|---|---|
| **v0.6.1** | Текущая базовая карта |
| **v0.6.2** | Базы + точки захвата + топология + ротация |
| **v0.6.3** | Рельеф + дороги + рампы + карманы + боевые зоны |
| **v0.6.4** | Граница + окружение + ресурсы |
| **v0.6.5** | Полная Dominion-симуляция + баланс |
| **v0.6.6** | Финальная проверка + экспорт + MAP LOCK |
| **v0.7.0** | Unreal Engine 5 |

---

# PHASE 2 — UNREAL ENGINE 5

# v0.7.x

## v0.7.0 — UE5 FOUNDATION

- архитектура проекта UE5
- структура папок
- GameInstance
- GameMode
- GameState
- PlayerController
- PlayerState
- Character/Pawn foundation
- Team foundation
- Gameplay Data Architecture
- Map Data Architecture
- Blender → UE5 pipeline
- автоматическая проверка импорта
- build/test baseline

## v0.7.1 — ИМПОРТ КАРТЫ

- Terrain
- Objectives
- Bases
- Roads
- Ramps
- Rocks
- Pockets
- Boundary
- Environment
- Materials
- Collision

## v0.7.2 — UE5 MAP GAMEPLAY

- Map Actor
- Objective Actors
- Base Actors
- Pocket Actors
- Map Resources
- Speed Shrines
- Health Relics
- Central Resource

## v0.7.3 — НАВИГАЦИЯ

- NavMesh
- Hero Navigation
- Minion Navigation
- Objective Navigation
- Pocket Navigation
- Dynamic Obstacles
- Navigation Debug

## v0.7.4 — GAMEPLAY FRAMEWORK

- Match
- Teams
- Objectives
- Events
- Gameplay Tags
- Data
- Spawn
- Debug

## v0.7.5 — ИНТЕГРАЦИЯ КАРТЫ

- 5 objectives
- 2 bases
- routes
- resources
- objective events
- map events
- replication foundation

## v0.7.6 — PLAYER FOUNDATION

- Character
- Movement
- Camera
- Input
- Health
- Death
- Respawn
- Spawn

## v0.7.7 — COMBAT FOUNDATION

- Targeting
- Basic Attack
- Damage
- Armor
- Resistance
- Death
- Combat Events

## v0.7.8 — MINION FOUNDATION

- Spawn
- Navigation
- Waves
- Melee
- Ranged
- Targeting
- Combat
- Objective Pressure

## v0.7.9 — UE5 FOUNDATION LOCK

Полностью рабочая основа:

**Map + Player + Navigation + Combat Foundation + Minions**

---

# PHASE 3 — DOMINION GAMEPLAY

# v0.8.x

## v0.8.0 — СИСТЕМА ЗАХВАТА

- Neutral
- Capture
- Neutralization
- Contest
- Capture Interruption
- Multi-player Capture
- Capture Progress
- Capture State
- Replication

## v0.8.1 — ВОЗВРАТ ТОЧКИ

- Neutral Decay
- Abandoned Point
- Partial Progress
- Ownership State

## v0.8.2 — ОБОРОНА OBJECTIVES

- Objective Attack
- Objective Defense
- Objective Damage
- Objective Disable During Neutralization

## v0.8.3 — СИСТЕМА СОСЕДНИХ МИНЬОНОВ

- Point Adjacency
- Minion Spawning
- Target Objective
- Wave Generation
- Objective Capture Pressure

## v0.8.4 — СИСТЕМА TICKETS

- Starting Tickets
- Point-Control Drain
- Difference-Based Drain
- Kill Contribution
- Victory Condition

## v0.8.5 — РЕСУРСЫ DOMINION

- Speed Shrine
- Health Relic
- Central Greater Relic equivalent

## v0.8.6 — OBJECTIVE QUEST SYSTEM

- Objective Challenge
- Attack Target
- Defense Target
- Reward
- Team Buff

## v0.8.7 — MATCH FLOW

- Countdown
- Spawn
- Active Match
- Victory
- Defeat
- Restart

## v0.8.8 — DOMINION AUTOMATED TESTS

- Capture Tests
- Ticket Tests
- Objective Tests
- Minion Tests
- Win/Loss Tests
- Replication Tests
- Full Match Tests

## v0.8.9 — DOMINION CORE LOCK

Capture + Objectives + Tickets + Match Flow locked.

---

# PHASE 4 — PLAYER

# v0.9.x

- Movement
- Camera
- Input
- Health
- Damage
- Death
- Respawn
- Spawn
- Team
- Player State

---

# PHASE 5 — COMBAT

# v0.10.x

- Targeting
- Basic Attack
- Range
- Cooldowns
- Damage
- Armor
- Resistance
- Critical Damage
- Death
- Combat Events
- Combat Logging

---

# PHASE 6 — HERO SYSTEM

# v0.11.x — ABILITY FRAMEWORK

- Ability Base
- Cooldown
- Resource
- Targeting
- Projectile
- AOE
- Buff
- Debuff
- Crowd Control
- Ability UI
- Ability Events

# v0.12.x — HERO #1

- Hero Data
- Stats
- Basic Attack
- Ability 1
- Ability 2
- Ability 3
- Ultimate
- Animation
- VFX
- SFX
- Testing

---

# PHASE 7 — MINIONS

# v0.13.x

- Spawn System
- Wave System
- Melee Minions
- Ranged Minions
- Targeting
- Navigation
- Combat
- Objective Interaction
- Rewards
- Balance
- Deathball Interaction

---

# PHASE 8 — ECONOMY / ITEMS

# v0.14.x — ECONOMY

- Gold
- XP
- Kill Rewards
- Objective Rewards
- Minion Rewards
- Passive Income
- Scaling
- Economy Events
- Economy UI

# v0.15.x — ITEMS

- Item Database
- Item Stats
- Shop
- Purchase
- Inventory
- Equipment
- Item Effects
- Shop UI
- Item Balance

---

# PHASE 9 — FULL 5V5

# v0.16.x — TEAM SYSTEM

- Blue Team
- Red Team
- Roster
- Spawn
- Ownership
- Team Events
- Scoreboard

# v0.17.x — COMPLETE MATCH

- Match Start
- Early Game
- Mid Game
- Late Game
- Victory
- Defeat
- Restart
- Full Automated Match

---

# PHASE 10 — GAME MODES

# v0.18.x — STATIC MODE

# v0.19.x — HYBRID MODE

# v0.20.x — DYNAMIC MODE

---

# PHASE 11 — NETWORK

# v0.21.x — MULTIPLAYER FOUNDATION

- Replication
- Server Authority
- Player Replication
- Combat Replication
- Ability Replication
- Objective Replication
- Minion Replication
- Economy Replication

# v0.22.x — ONLINE MATCH

- Lobby
- Match Creation
- Joining
- Teams
- Disconnect
- Reconnect
- Match Completion

---

# PHASE 12 — UI

# v0.23.x — GAME UI

- HUD
- 5 Objectives
- Tickets
- Minimap
- Hero HUD
- Abilities
- Items
- Scoreboard
- Death Screen
- Match End Screen

---

# PHASE 13 — GAME FEEL

# v0.24.x

- Hit Feedback
- Damage Feedback
- Movement Feel
- Camera
- Ability Feedback
- Objective VFX
- Audio
- Screen Effects
- Combat Feedback

---

# PHASE 14 — CONTENT

# v0.25.x — HERO ROSTER

- Hero #2–#8
- Hero Balance

# v0.26.x — CONTENT SYSTEM

- Animation
- VFX
- SFX
- Environment
- Props
- Materials
- Lighting
- Optimization

---

# PHASE 15 — BALANCE

# v0.27.x

- Map Balance
- Hero Balance
- Item Balance
- Economy Balance
- Objective Balance
- Minion Balance
- Deathball Balance
- Snowball Balance
- Comeback Balance
- Match Duration
- Rotation Balance

---

# PHASE 16 — QA / PERFORMANCE

# v0.28.x — QA FOUNDATION

- Unit Tests
- Gameplay Tests
- Map Tests
- Navigation Tests
- Combat Tests
- Network Tests
- Performance Tests
- Regression Tests

# v0.29.x — PERFORMANCE

- CPU
- GPU
- Memory
- Network
- Draw Calls
- Nanite
- Lumen
- Large Combat
- 5v5 Stress Test

---

# PHASE 17 — ALPHA

# v0.30.0 — INTERNAL ALPHA

Полный playable build:

- 5v5
- 5 objectives
- heroes
- combat
- abilities
- minions
- economy
- items
- tickets
- Static Mode

# v0.31.x — ALPHA BALANCE

# v0.32.x — ALPHA CONTENT

# v0.33.x — ALPHA PERFORMANCE

# v0.34.x — ALPHA NETWORK

# v0.35.x — ALPHA QA

# v0.36.x — ALPHA POLISH

# v0.37.x — ALPHA CANDIDATE

# v0.38.x — ALPHA LOCK

# v0.39.x — PRE-BETA

---

# PHASE 18 — BETA

# v0.40.0 — BETA FOUNDATION

# v0.41.x — BETA BALANCE

# v0.42.x — BETA HEROES

# v0.43.x — BETA ITEMS

# v0.44.x — BETA MAP

# v0.45.x — BETA NETWORK

# v0.46.x — BETA UI

# v0.47.x — BETA PERFORMANCE

# v0.48.x — BETA QA

# v0.49.0 — RELEASE CANDIDATE

# v0.50.0 — BETA

---

# PHASE 19 — RELEASE

# v0.90.0 — RELEASE CANDIDATE

# v0.91–v0.98 — FINAL POLISH

Только:

- bug fixes
- balance fixes
- performance fixes
- server stability
- UX fixes
- regression fixes

Никаких новых крупных систем.

# v0.99.0 — GOLD MASTER

# v1.0.0 — AETHERFLOW RELEASE

---

# КЛЮЧЕВОЙ ПРИНЦИП DOMINION ДЛЯ AETHERFLOW

AetherFlow не копирует Crystal Scar визуально. Используются её сильные игровые принципы:

1. 5 capture points.
2. 5v5.
3. Capture-and-hold.
4. Нет классических трёх MOBA-линий.
5. Постоянная ротация между objectives.
6. Контроль территории важнее количества убийств.
7. Соседние objectives взаимодействуют.
8. Захваченная точка создаёт давление на соседнюю вражескую точку.
9. Существуют быстрые внешние и более рискованные внутренние маршруты.
10. Backdoor возможен, но рискован.
11. Deathball не должен автоматически выигрывать карту.
12. Split pressure должен иметь значение.
13. Ресурсы должны создавать дополнительные причины для ротации.
14. Контроль карты должен постоянно меняться.

---

# ФИНАЛЬНАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ

**v0.6.1** — текущая карта

↓

**v0.6.2** — базы + точки захвата + топология + ротация

↓

**v0.6.3** — рельеф + дороги + рампы + карманы + боевые зоны

↓

**v0.6.4** — граница + окружение + ресурсы

↓

**v0.6.5** — полная Dominion-симуляция + баланс

↓

**v0.6.6** — финальная проверка + экспорт + MAP LOCK

↓

# v0.7.0 — UE5 FOUNDATION

↓

# v0.8.0 — DOMINION GAMEPLAY

↓

# v0.9.0 — PLAYER

↓

# v0.10.0 — COMBAT

↓

# v0.11.0 — ABILITIES

↓

# v0.12.0 — HERO #1

↓

# v0.13.0 — MINIONS

↓

# v0.14.0 — ECONOMY

↓

# v0.15.0 — ITEMS

↓

# v0.16.0 — TEAMS

↓

# v0.17.0 — COMPLETE 5V5

↓

# v0.18–0.20 — GAME MODES

↓

# v0.21–0.22 — MULTIPLAYER / ONLINE

↓

# v0.23–0.29 — UI / GAME FEEL / CONTENT / BALANCE / QA / PERFORMANCE

↓

# v0.30+ — ALPHA

↓

# v0.40+ — BETA

↓

# v0.90+ — RELEASE

↓

# v1.0.0 — AETHERFLOW
