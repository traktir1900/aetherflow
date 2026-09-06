"""
AetherFlow :: core/context.py
Per-run context: config, layout, collections, materials and a DETERMINISTIC
random generator.

Determinism: every module that needs randomness must draw from ctx.rng
(a random.Random seeded from config["seed"]).  Same config + seed therefore
yields the same map.  Never use the global `random` functions.
"""
import random


class MapContext:
    def __init__(self, config, project_root=""):
        self.config = config
        self.project_root = project_root
        self.layout = {}
        self.collections = {}
        self.materials = {}
        self.generated_objects = []        # registry for export / validation
        self.pockets = []                  # pocket metadata (v0.6.1)
        self.capture_buttons = {}          # point name -> logical capture button object
        self._rng = random.Random(int(config.get("seed", 1337)))

    # -- deterministic randomness -------------------------------------------
    @property
    def rng(self):
        return self._rng

    def reseed(self):
        """Restart the stream (e.g. at the start of a fresh generation)."""
        self._rng = random.Random(int(self.config.get("seed", 1337)))

    def rand(self, lo, hi):
        return self._rng.uniform(lo, hi)

    # -- lookups -------------------------------------------------------------
    def get_collection(self, name):
        return self.collections.get(name)

    def get_material(self, name):
        return self.materials.get(name)

    # -- object registry ------------------------------------------------------
    def register(self, obj, kind, dims=None, meta=None):
        """Record a generated object for validation + map_data.json export."""
        self.generated_objects.append({
            "object": obj,
            "name": getattr(obj, "name", str(obj)),
            "type": kind,
            "dimensions": dims,
            "meta": meta or {},
        })
        return obj
