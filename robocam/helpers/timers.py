import time
import abc


class Timer(abc.ABC):

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        """
        abstract base class for all Timers. 
        All are called via the __call__ method
        """
        pass

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """
        all call methods should allow for overriding args in

        """
        return True


class SmartSleeper(Timer):

    def __init__(self, wait=1 / 30):
        """
        if time since last call is less than wait, sleeps for the difference. 
        """
        self.wait = wait
        self.tick = None

    def __call__(self, wait=None):
        _wait = wait if wait is not None else self.wait
        if self.tick is None:
            self.tick = time.time()
        else:
            if time.time() - self.tick < _wait:
                time.sleep(_wait - time.time() + self.tick)
            self.tick = time.time()


class TimeSinceLast(Timer):

    def __init__(self):
        """
        returns the time elapsed since the last time it was called
        """
        self._tick = time.time()
        self.on = False

    def __call__(self):
        if self.on is False:
            self._tick = time.time()
            self.on = True
            return 0

        tock = time.time()
        out: float = tock - self._tick
        self._tick = tock
        return out


class TimeSinceFirst(Timer):

    def __init__(self, chop=False, rnd=False):
        """
        returns the time elapsed since the first call
        """
        self._tick = None
        self.chop = chop
        self.rnd = rnd

    def reset(self):
        self._tick = None

    def start(self):
        self()
        return self

    def __call__(self):
        if self._tick is None:
            self._tick = time.time()
            return 0.

        t_elapsed = time.time() - self._tick
        if self.chop is False and self.rnd is False:
            return t_elapsed
        elif self.chop is True:
            return int(t_elapsed)
        else:
            return round(t_elapsed, self.rnd)


class FunctionTimer(Timer):

    def __init__(self, function):
        """

        :param function: uncalled function
        """
        self.function = function
        self._time = 0

    @property
    def time(self):
        return self._time

    def __call__(self, *args, **kwargs):
        tick = time.time()
        out = self.function(*args, **kwargs)
        self._time = time.time() - tick
        return out


class SinceFirstBool(TimeSinceFirst):
    """
    return True if time since first call > wait else False
    """
    def __init__(self, wait=1, *args,**kwargs):
        super().__init__(*args, **kwargs)
        self.wait = wait

    def __call__(self):
        if super().__call__() > self.wait:
            return True
        else:
            return False


class CallHzLimiter(Timer):

    def __init__(self, wait=1 / 3, first=True):
        """
        returns true wait is over else returns False
        :param wait: float in seconds
        """
        self.wait = wait
        self._tick = 0
        self.first = True

    def __call__(self, wait=None):

        _wait = self.wait if wait is None else wait
        if time.time() - self._tick >= _wait:
            self._tick = time.time()
            return True
        else:
            return False


class Blinker(Timer):

    def __init__(self, cycle=.5):
        """
        returns True during on_time and False during off_time
        :type cycle: if list : time_on, time_off = cycle
                     if double : time_on = time_off = cycle
        """
        self.cycle = cycle
        self.on = False
        self._tick = 0

    @property
    def cycle(self):
        return self._cycle

    @cycle.setter
    def cycle(self, new_cycle):
        if isinstance(new_cycle, (int, float)):
            self._cycle = [new_cycle] * 2
        else:
            self._cycle = new_cycle

    def __call__(self):

        if self.on is True:
            if time.time() - self._tick > self._cycle[0]:
                self._tick = time.time()
                self.on = False

            return True
        else:
            if time.time() - self._tick > self._cycle[1]:
                self._tick = time.time()
                self.on = True

            return False

#todo 
class TimedCycle:

    def __init__(self,
                 mini=0,
                 maxi=255,
                 start=0,
                 dir = 1,
                 cycle_t = 1,
                 max_ups = 60,
                 repeat = True,
                 updown = False, 
                 end_value = None
                 ):

        self.mini = mini
        self.maxi = maxi
        self._i = start
        self.dir = dir
        self.start = start
        self.max_ups = max_ups
        self.updown = updown
        self.end_value = end_value

        self.length = (maxi - mini + 1)
        self.cycle_t = cycle_t
        self.speed =  self.length/ self.cycle_t
        self.repeat = repeat
        self.complete = False

        self.ups_timer = CallHzLimiter(1/max_ups)
        self.last_timer = TimeSinceLast()
        self.total_steps = 0

    @property
    def i(self):
        return int(self._i)

    def reset(self):
        self.ups_timer = CallHzLimiter(1/self.max_ups)
        self.last_timer = TimeSinceLast()
        self.complete = False
        self._i = self.start
        self.total_steps = 0

    def __call__(self):

        if self.ups_timer() is True:

            tp = self.last_timer()
            self._i = self._i + self.speed * tp * self.dir
            self.last_step = self.speed * tp   
            self.total_steps += self.last_step

            if self.updown is False:
                self._one_direction_counter()
            else:
                self._up_down_counter()

        return self.i

    def _one_direction_counter(self):

        if self.repeat is True and self._i >= self.maxi:
            self._i = self.mini

        elif self.repeat is True and self._i <= self.mini:
            self._i = self.maxi

        elif self.repeat is False and self._i >= self.maxi:
            self._i = self.maxi
            self.complete = True

        elif self.repeat is False and self._i <= self.mini:
            self._i = self.mini
            self.complete = True

    def _up_down_counter(self):

        if self._i > self.maxi:# and self.repeat is False:
            self._i = self.maxi
            self.dir *=-1

        elif self._i < self.mini:# and self.repeat is False:
            self._i = self.mini
            self.dir *= -1