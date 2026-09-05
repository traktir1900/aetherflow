"""
Minimal mathutils.Vector stub — just enough for AetherFlow's engine-free
modules (layout, heightmap, navigation, simulation, validation, export) to
run under plain Python 3 for automated tests.  Blender modules that need
bmesh/bpy are NOT covered and require a real Blender run.
"""
import math


class Vector:
    __slots__ = ("_v",)

    def __init__(self, seq):
        seq = list(seq)
        if len(seq) == 2:
            seq.append(0.0)
        if len(seq) != 3:
            raise ValueError("Vector stub expects 2 or 3 components")
        self._v = [float(a) for a in seq]

    # -- components -----------------------------------------------------------
    @property
    def x(self):
        return self._v[0]

    @x.setter
    def x(self, v):
        self._v[0] = float(v)

    @property
    def y(self):
        return self._v[1]

    @y.setter
    def y(self, v):
        self._v[1] = float(v)

    @property
    def z(self):
        return self._v[2]

    @z.setter
    def z(self, v):
        self._v[2] = float(v)

    # -- ops ---------------------------------------------------------------------
    def __add__(self, o):
        return Vector((self.x + o.x, self.y + o.y, self.z + o.z))

    def __sub__(self, o):
        return Vector((self.x - o.x, self.y - o.y, self.z - o.z))

    def __mul__(self, s):
        return Vector((self.x * s, self.y * s, self.z * s))

    def __rmul__(self, s):
        return self.__mul__(s)

    def __truediv__(self, s):
        return Vector((self.x / s, self.y / s, self.z / s))

    def __neg__(self):
        return Vector((-self.x, -self.y, -self.z))

    def __iter__(self):
        return iter(self._v)

    def __len__(self):
        return 3

    def __getitem__(self, i):
        return self._v[i]

    def __setitem__(self, i, v):
        self._v[i] = float(v)

    def __repr__(self):
        return "Vector({:.4f}, {:.4f}, {:.4f})".format(*self._v)

    # -- geometry -------------------------------------------------------------------
    @property
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self):
        l = self.length
        if l < 1e-12:
            return Vector((0.0, 0.0, 0.0))
        return Vector((self.x / l, self.y / l, self.z / l))

    def dot(self, o):
        return self.x * o.x + self.y * o.y + self.z * o.z

    def copy(self):
        return Vector(self._v)
