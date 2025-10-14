The data from the moisture sensors is **stored in memory** inside the `Moisture` class, specifically in the `_history` attribute. Here’s how it works:

---

### 1. **Moisture Class Internal Storage**

In [moisture.py](https://github.com/jasonmvega/jasonvegapi/blob/main/moisture.py):

```python name=moisture.py url=https://github.com/jasonmvega/jasonvegapi/blob/main/moisture.py
class Moisture(object):
    def __init__(self, channel=1, wet_point=None, dry_point=None):
        ...
        self._history = []
        self._history_length = 200
        ...
```

- The attribute `self._history` is a Python list that holds the most recent moisture readings (pulses/sec).
- The length of this history is capped at 200 readings (`self._history_length = 200`).

---

### 2. **How Readings Are Stored**

The readings are added in the `_event_handler` method:

```python
def _event_handler(self, pin):
    self._count += 1
    self._last_pulse = time.time()
    if self._time_elapsed >= 1.0:
        self._reading = self._count / self._time_elapsed
        self._history.insert(0, self._reading)
        self._history = self._history[:self._history_length]
        self._count = 0
        self._time_last_reading = time.time()
        self._new_data = True
```

- Every second (`self._time_elapsed >= 1.0`), a new reading is calculated and inserted at the start of `self._history`.
- The history list is then truncated to the last 200 readings.

---

### 3. **Accessing Data**

- The `history` property returns a normalized version of the readings (as saturation values between 0.0 and 1.0).
- There is **no persistent storage** (file/database) for these readings; they exist only in RAM while the program runs.

---

### 4. **Usage in Other Parts of the Program**

In [grow-monitor.py](https://github.com/jasonmvega/jasonvegapi/blob/main/grow-monitor.py), when graphing moisture levels:

```python
for x, value in enumerate(self.channel.sensor.history[:graph_width]):
    ...
```
- The graph uses the in-memory `history` data from each `Moisture` instance.

---

## **Summary Table**

| Data Location      | Type      | Used for            | Persistence      |
|--------------------|-----------|---------------------|------------------|
| `self._history`    | List      | Recent readings     | In-memory only   |
| `history` property | List      | Normalized values   | In-memory only   |

---

**TL;DR:**  
The moisture sensor data is stored in the `_history` list inside each `Moisture` object, in memory only (not written to disk).
