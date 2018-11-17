from typing import Union, Tuple, Iterable, Optional

import tensorflow as tf

LowerType = Union[Tuple[Tuple[float, ...]], Tuple[float, ...]]
UpperType = Union[Tuple[Tuple[float, ...]], Tuple[float, ...]]
LimitsType = Union[Tuple[Tuple[float, ...]], Tuple[float, ...]]
DimsType = Union[Tuple[int, ...], Tuple[int, ...]]
XType = Union[float, tf.Tensor]
ParamsType = Optional[Iterable['Parameter']]
ParamsOrNameType = Optional[Union[ParamsType, Iterable[str]]]
SessionType = Optional[tf.Session]
BaseObjectType = Union['Parameter', 'Function', 'PDF']
