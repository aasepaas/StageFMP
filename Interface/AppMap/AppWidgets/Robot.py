class Robot:
    """Managaes singular robot data such as status adn"""
    def __init__(self, name):
        self.name = name
        self._current_position = []
        self._current_status = None


    def set_status(self, status):
        self._current_status = status

    def get_status(self):
        return self._current_status

    def get_current_position(self):
        return self._current_position

    def set_current_position(self, coords):
        self._current_position = coords


        




