import itertools

import tensorflow as tf

from zfit.core.basefunc import BaseFunc
from zfit.util.container import convert_to_container


class SimpleFunction(BaseFunc):

    def __init__(self, func, name="Function", **parameters):
        super().__init__(name=name, **parameters)
        self._value_func = self._check_input_x_function(func)

    def _value(self, x):
        return self._value_func(x, **self.get_parameters())


class BaseFunctorFunc(BaseFunc):
    def __init__(self, funcs, name="BaseFunctorFunc", **kwargs):
        super().__init__(name=name, **kwargs)
        funcs = convert_to_container(funcs)
        self.funcs = funcs

    def get_dependents(self, only_floating=True):  # TODO: change recursive to `only_floating`?
        dependents = super().get_dependents(only_floating=only_floating)  # get the own parameter dependents
        func_dependents = (func.get_dependents(only_floating=only_floating) for func in self.funcs)
        func_dependents = set(itertools.chain.from_iterable(func_dependents))  # flatten

        return dependents.union(func_dependents)


class SumFunc(BaseFunctorFunc):
    def __init__(self, funcs, dims=None, name="SumFunc", **kwargs):
        super().__init__(funcs=funcs, name=name, **kwargs)
        self.dims = dims

    def _value(self, x):
        sum_funcs = tf.accumulate_n([func(x) for func in self.funcs])
        return sum_funcs


class ProdFunc(BaseFunctorFunc):
    def __init__(self, funcs, name="SumFunc", **kwargs):
        super().__init__(funcs=funcs, name=name, **kwargs)

    def _value(self, x):
        value = self.funcs[0](x)
        for func in self.funcs[1:]:
            value *= func(x)
        return value
