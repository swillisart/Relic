from sequencePath import sequencePath as Path
import glm


class AttributeDescriptor(object):
    def __init__(self, plug):
        self.plug = plug

    def __get__(self, obj, objType):
        value = None # obj.data(role=polymorphicItem.Object)
        return getattr(value, self.plug)

    def __set__(self, obj, value):
        # SET DATA # item = obj.data(role=polymorphicItem.Object)
        setattr(item, self.plug, value)
        # SET DATA # obj.setData(item, polymorphicItem.Object)

    @staticmethod
    def buildNodeAttr(cls, attr):
        setattr(cls, attr, AttributeDescriptor(attr))


class ImageDimensions(glm.vec2):
    def __init__(self, width, height, channels=1):
        super(ImageDimensions, self).__init__(width, height)
        self.channels = channels
    
    @classmethod
    def fromArray(cls, array):
        h, w, c = array.shape
        obj = cls(w, h, channels=c)
        return obj

    def makeDivisble(self):
        self.x = self.divisible_width

    @property
    def divisible_width(self):
        return self.x - (self.x % 16)

    @property
    def aspect(self):
        return self.w / self.h

    @property
    def aspectReversed(self):
        return self.h / self.w

    @property
    def w(self):
        return int(self.x)

    @w.setter
    def w(self, value):
        self.x = value

    @property
    def h(self):
        return int(self.y)

    @h.setter
    def h(self, value):
        self.y = value
