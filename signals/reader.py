import json

class SignalReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._file = None
        self._position = 0

    def start(self, reset_pointer=False):
        self._file = open(self.filepath, "r")
        if reset_pointer:
            self._file.seek(0)
        else:
            self._file.seek(0, 2)
        self._position = self._file.tell()

    def read_new_signals(self):
        self._file.seek(self._position)
        while line := self._file.readline():
            self._position = self._file.tell()
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

    def close(self):
        if self._file:
            self._file.close()
