import inspect

class EventBus():
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_name, callback):
        self._subscribers.setdefault(event_name, []).append(callback)

    def publish(self, event_name, data=None):
        import logging
        logger = logging.getLogger(__name__)
        for callback in self._subscribers.get(event_name, []):
            try:
                sig = inspect.signature(callback)
                if len(sig.parameters) == 0:
                    callback()
                else:
                    callback(data)
            except Exception as e:
                logger.exception("EventBus: error en suscriptor de '%s': %s", event_name, e)