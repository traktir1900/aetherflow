
class ValidationResult:
    def __init__(self, name):
        self.name = name
        self.errors = []
        self.warnings = []
        self.duration = 0.0
        
    @property
    def ok(self):
        return len(self.errors) == 0
