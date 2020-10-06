import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PtCalculator:
    def __init__(self, r_0=100):
        self.a = 3.9083e-3
        self.b = -5.7750e-7
        self.c = -4.1830e-12
        self.r_0 = r_0
        self._feed_temperature = 0

    def _normr(self, temperature):
        normr = 1 + self.a * temperature
        normr += self.b * temperature**2
        if temperature < 0:
            normr += self.c * (temperature - 100) * temperature**3

        return normr

    def _dnormr_dt(self, temperature):
        value = self.a + 2 * self.b * temperature
        if temperature < 0:
            value += self.c * (4 * temperature - 300) * temperature**2

        return value

    def get_temperature(self, resistance, error=1e-7, max_iter=100):
        """ Get temperature from resistance value with newton method"""
        temperature = self._feed_temperature
        norm_r = resistance / self.r_0
        for iteration in range(max_iter):
            delta_t = (
                - (self._norm(temperature) - norm_r) /
                self._dnorm_dt(temperature)
                )
            temperature += delta_t
            if abs(delta_t) < error:
                self._feed_temperature = temperature
                logging.debug(f'Found temperature with error less than '
                              f'{delta_t} after {iteration} iterations')
                return temperature
        self._feed_temperature  = 0
        raise Exception(f'Not found temperature for resistance {resistance}')

    def get_resistance(self, temperature):
        return self.r_0 * self._normr(temperature)

    def get__dresistance__dtemperature(self, temperature):
        return self.r_0 * self._dnormr_dt(temperature)

    def get_dtemperature_dresistance(self, resistance):
        temperature = self.get_temperature(resistance)
        return 1 / self.get_dresistance_dtemperature(temperature)
