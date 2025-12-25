# modules/вселенная.py
# Мультивселенная проекта "РаСвет"
# Связь не через пространство, а через резонанс

import uuid
from modules.время import TIME

class UniverseNode:
    def __init__(self, name, level=0):
        self.name = name
        self.level = level              # Уровень плотности / проявленности
        self.id = str(uuid.uuid4())
        self.created_at = None          # Не фиксируем рождение
        self.resonance_links = set()    # Связанные вселенные
        self.data = {}

    def link(self, other_universe_id):
        self.resonance_links.add(other_universe_id)

    def receive_seed(self, seed):
        """
        Принимает Расцвет / Идею / Импульс
        """
        self.data.setdefault("seeds", []).append({
            "seed": seed,
            "received_at": TIME.unix()
        })


class Multiverse:
    def __init__(self):
        self.universes = {}

    def create_universe(self, name, level=0):
        u = UniverseNode(name=name, level=level)
        self.universes[u.id] = u
        return u.id

    def resonate(self, source_id, target_id, seed):
        """
        Мгновенная передача через резонанс
        """
        if source_id in self.universes and target_id in self.universes:
            self.universes[target_id].receive_seed(seed)
            self.universes[source_id].link(target_id)
            self.universes[target_id].link(source_id)

    def state(self):
        return {
            uid: {
                "name": u.name,
                "level": u.level,
                "links": list(u.resonance_links),
                "seeds": len(u.data.get("seeds", []))
            }
            for uid, u in self.universes.items()
        }


# Глобальное поле мультивселенной
MULTIVERSE = Multiverse()
