from datetime import date

class DeviceDTO:
    def __init__(self, id: int, created_at: date):
        self.id = id
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
        }