# Class that represents a location in the map

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def getX(self):
        return self.x
    
    def setX(self, x):
        self.x = x

    def getY(self):
        return self.y
    
    def setY(self, y):
        self.y = y

    def __str__(self):
        return "Locations are- X: " + self.x + "; Y: " + self.y