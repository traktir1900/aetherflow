# AetherFlow 0.6.4.0 — VerdantTrail Natural Perimeter

Replaces the procedural placeholder natural-perimeter assets with real linked
VerdantTrail collections already attached to the AetherFlow Blender scene.

Expected linked collections:
- cliffs_boulders
- rocks
- island_tree_01
- jacaranda_tree
- tree_small_02
- shrub_01
- shrub_02
- shrub_03
- shrub_04
- grass_medium_02
- hanging_grass
- plants_groups

The active pipeline invokes `geometry/natural_perimeter.py` after the global
wall is generated. No gameplay geometry, navigation, simulation, pockets,
bases, Altar or wall geometry is modified by the natural-perimeter pass.
