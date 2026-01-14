import inspect

class EventBus():
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_name, callback):
        self._subscribers.setdefault(event_name, []).append(callback)

    def publish(self, event_name, data=None):
        for callback in self._subscribers.get(event_name, []):
            sig = inspect.signature(callback)
            if len(sig.parameters) == 0:
                callback()
            else:
                callback(data)