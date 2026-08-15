class MapContext:
    def __init__(self, config, project_dir):
        self.config = config
        self.project_dir = project_dir
        self.layout = {}
        self.collections = {}
        self.materials = {}

    def get_collection(self, name):
        return self.collections.get(name)

    def get_material(self, name):
        return self.materials.get(name)
