# eventbus.py
import queue

# Shared queue for results (used by tcp_client & app)
result_event_queue = queue.Queue()

def push_result(cam_id, data):
    """
    Push result data for a station to the queue.
    data can be:
      - a dict (recommended): {"result":"OK", "defects": {...}, "dimensions": {...}}
      - a string: "OK" or "NOK"
    """
    message = {"cam_id": cam_id}
    if isinstance(data, dict):
        message.update(data)
    else:
        message["result"] = data
    result_event_queue.put(message)
