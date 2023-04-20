#!/usr/bin/env python

from itertools import product

import numpy as np

from olympus.surfaces import AbstractSurface


class Dejong(AbstractSurface):
    def __init__(self, param_dim=2, noise=None):
        """Dejong function.

        Args:
            param_dim (int): Number of input dimensions. Default is 2.
            noise (Noise): Noise object that injects noise into the evaluations of the surface. Default is None.
        """
        value_dim = 1
        task = 'regression'
        AbstractSurface.__init__(**locals())

    @property
    def minima(self):
        # minimum at the centre
        params = [0.5] * self.param_dim
        value = self._run(params)
        return [{"params": params, "value": value}]

    @property
    def maxima(self):
        # maxima at the corners
        maxima = []
        params = product([0, 1], repeat=self.param_dim)
        for param in params:
            param = list(param)
            value = self._run(param)
            maxima.append({"params": param, "value": value})
        return maxima

    def _run(self, params):
        params = np.array(params)
        params = 10 * params - 5  # rescale onto [-5, 5]
        result = np.sum(np.abs(params) ** 0.5)
        if self.noise is None:
            return result
        else:
            return self.noise(result)
