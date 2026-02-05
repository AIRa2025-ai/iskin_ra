import heapq

class RaPriorityQueue:
    """
    Очередь событий по важности
    """

    PRIORITY = {
        "critical": 0,
        "high": 1,
        "normal": 2,
        "low": 3
    }

    def __init__(self):
        self.queue = []

    def push(self, event: dict):
        priority = self.PRIORITY.get(event.get("priority", "normal"), 2)
        heapq.heappush(self.queue, (priority, event))

    def pop(self):
        if not self.queue:
            return None
        return heapq.heappop(self.queue)[1]
