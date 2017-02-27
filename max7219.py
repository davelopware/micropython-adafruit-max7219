import time

_NOOP = const(0)
_DIGIT0 = const(1)
_DIGIT1 = const(2)
_DIGIT2 = const(3)
_DIGIT3 = const(4)
_DIGIT4 = const(5)
_DIGIT5 = const(6)
_DIGIT6 = const(7)
_DIGIT7 = const(8)
_DECODEMODE = const(9)
_INTENSITY = const(10)
_SCANLIMIT = const(11)
_SHUTDOWN = const(12)
_DISPLAYTEST = const(15)

class Matrix8x8Chain:
    def __init__(self, spi, cs, chain_length = 1, auto_init=True):
        self.spi = spi
        self.cs = cs
        # self.cs.init(cs.OUT, True)  // this doesn't seem to work on HCS, so leave it for the caller to decide
        self.chain_length = chain_length
        self.buffer = []  # 0 indexed array of 8x8 buffers
        self._init_buffers()
        if (auto_init):
            self.init()

    def _init_buffers():
        for i in range(chain_length):
            self.buffer.append(bytearray(8))

    def _begin(self):
        print(">")
        self.cs.low()
        time.sleep(0.001)

    def _commit(self):
        print("<")
        self.cs.high()
        time.sleep(0.001)

    def _raw_noop(self):
        self.spi.write(bytearray([_NOOP, 0]))

    def _register_raw(self, command, data, auto_commit=True):
        if (auto_commit):
            self._begin()

        # print("Sending %s:%s" % (hex(command), hex(data)))
        self.spi.write(bytearray([command, data]))

        if (auto_commit):
            self._commit()

    def _register_target(self, target, command, data):
        self._begin()

        for target_index in range(self.chain_length-1,-1,-1):
            if (target_index == target):
                # print("Sending %s:%s to target %d" % (hex(command), hex(data), target))
                self.spi.write(bytearray([command, data]))
            else:
                self._raw_noop()

        self._commit()

    def _targets_helper(targets):
        if isinstance(targets, list) == False:
            if target = None:
                targets = range(self.chain_length)
            else:
                targets = [target]
        return targets

    def init(self):
        for command, data in (
            (_SHUTDOWN, 0),
            (_DISPLAYTEST, 0),
            (_SCANLIMIT, 7),
            (_DECODEMODE, 0),
            (_SHUTDOWN, 1),
        ):
            self._register_raw(command, data)
            self._register_raw(command, data)
            self._register_raw(command, data)
            self._register_raw(command, data)

    def noop(self, auto_commit=True):
        if (auto_commit):
            self._begin()

        self._raw_noop()

        if (auto_commit):
            self._commit()

    def brightness(self, targets, value):
        if not 0<= value <= 15:
            raise ValueError("Brightness out of range")
        targets = self._targets_helper(targets)
        for target in targets:
            self._register_target(_INTENSITY, target, value)

    def buf_fill(self, targets, color):
        data = 0xff if color else 0x00
        targets = self._targets_helper(targets)
        for target in targets:
            for y in range(8):
                self.buffer[target][y] = data

    def buf_pixel(self, target, x, y, color=None):
        if color is None:
            return bool(self.buffer[target][y] & 1 << x)
        elif color:
            self.buffer[target][y] |= 1 << x
        else:
            self.buffer[target][y] &= ~(1 << x)

    def buf_row(self, target, r, data):
        self.buffer[target][r] = data

    def update(self, delay=0):
#        self._begin()
        for y in range(8):
            self._begin()
            for target in range(self.chain_length-1,-1,-1):   # this counts back from the last in chain to the first
                self._register_raw(_DIGIT0 + y, self.buffer[target][y], False)
                time.sleep(delay)
            self._commit()
#        self._commit()

    def dump(self):
        for target in range(self.chain_length-1,-1,-1):   # this counts back from the last in chain to the first
            for y in range(8):
                print("[%d] %d : %s" % (target, y, bin(self.buffer[target][y])))
