class Qubit:
    """
    qBraid Qubit class
    """
    def __init__(self, index: int):
        self._index = index

    @property
    def index(self):
        return self._index
