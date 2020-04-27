class PtCalculator:
    def __init__(self, r_0=100, debug=False):
        self.a = 3.9083e-3
        self.b = -5.7750e-7
        self.c = -4.1830e-12
        self.r_0 = r_0
        self.debug = debug
        self._feed_temperature = 0

    def _f(self, norm_r, temperature):
        value = 1 - norm_r + self.a * temperature
        value += self.b * temperature**2
        if norm_r < 1:
            value += self.c * (temperature - 100) * temperature**3

        return value

    def _df(self, norm_r, temperature):
        value = self.a + 2 * self.b * temperature
        if norm_r < 1:
            value += self.c * (4 * temperature - 300) * temperature**2

        return value

    def get_temperature(self, resistance, error=1e-7, max_iter=100):
        """ Get temperature from resistance value with newton method"""
        temperature = self._feed_temperature
        norm_r = resistance / self.r_0
        for iteration in range(max_iter):
            delta_t = - self._f(norm_r,
                                temperature) / self._df(norm_r,
                                                        temperature)
            temperature += delta_t
            if abs(delta_t) < error:
                self._feed_temperature = temperature
                if self.debug:
                    return temperature, delta_t, iteration
                else:
                    return temperature

        self._feed_temperature  = 0

    def get_resistance(self, temperature):
        value = 1 + self.a * temperature + self.b * temperature**2
        if temperature < 0:
            value += self.c * (temperature - 100) * temperature**3
        return self.r_0 * value
