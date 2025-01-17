#  Copyright (c) 2023 zfit
from __future__ import annotations

import pydantic
import yaml

from zfit.util.warnings import warn_experimental_feature


class ZfitSerializable:
    hs3_type: str = None

    @classmethod
    def get_repr(cls) -> pydantic.BaseModel:
        from zfit.serialization import Serializer

        return Serializer.type_repr[cls.hs3_type]

    def to_orm(self):
        raise NotImplementedError


class NumpyArrayNotSerializableError(TypeError):
    pass


class SerializableMixin(ZfitSerializable):
    hs3 = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hs3 = type(self).hs3(self)

    def __init_subclass__(cls, **kwargs):
        cls.hs3 = create_HS3(cls)

    @warn_experimental_feature
    def to_yaml(self):
        """Convert the object to a yaml string.

        Returns:
            str: The yaml string.
        """
        json_obj = self.to_json()
        yaml_obj = yaml.safe_dump(json_obj)
        return yaml_obj

    @warn_experimental_feature
    def to_asdf(self):
        """Convert the object to an asdf file."""
        try:
            import asdf
        except ImportError:
            raise ImportError(
                "The asdf module is not installed. Please install zfit with the extra `hs3` (i.e. `pip install zfit[sh3]` or asdf directry to use this feature."
            )

        asdf_obj = asdf.AsdfFile(self.to_dict())
        return asdf_obj

    @classmethod
    @warn_experimental_feature
    def from_asdf(cls, asdf_obj):
        """Load an object from an asdf file."""

        asdf_tree = asdf_obj.tree
        # cleanup the asdf chunk
        asdf_tree.pop("asdf_library", None)
        asdf_tree.pop("history", None)
        orm = cls.from_dict(asdf_tree)
        return orm

    @warn_experimental_feature
    def to_json(self):
        """Convert the object to a json string.

        Returns:
            str: The json string.
        """
        from zfit.serialization import Serializer

        Serializer.initialize()
        repr = self.get_repr()
        orm = repr.from_orm(self)
        try:
            json_obj = orm.json(exclude_none=True, by_alias=True)
        except TypeError as error:
            if "Object of type 'ndarray' is not JSON serializable" in str(error):
                raise NumpyArrayNotSerializableError(
                    "The object you are trying to serialize contains numpy arrays. "
                    "This is not supported by json. Please use `to_asdf` (or `to_dict)` instead."
                )
            else:
                raise
        return json_obj

    @classmethod
    @warn_experimental_feature
    def from_json(cls, json: str) -> object:
        """Load an object from a json string.

        Args:
            json: Serialized object in a JSON string.

        Returns:
            The deserialized object.
        """
        from zfit.serialization import Serializer

        Serializer.initialize()
        orm = cls.get_repr().parse_raw(json)
        return orm.to_orm()

    @warn_experimental_feature
    def to_dict(self):
        """Convert the object to a nested dictionary structure.

        Returns:
               dict: The dictionary structure.
        """
        from zfit.serialization import Serializer

        Serializer.initialize()
        repr = self.get_repr()
        orm = repr.from_orm(self)
        return orm.dict(exclude_none=True, by_alias=True)

    @classmethod
    @warn_experimental_feature
    def from_dict(cls, dict_):
        """Creates an object from a dictionary structure as generated by `to_dict`.

        Args:
            dict_: Dictionary structure.

        Returns:
            The deserialized object.
        """
        from zfit.serialization import Serializer

        Serializer.initialize()
        orm = cls.get_repr().parse_obj(dict_)
        return orm.to_orm()

    @classmethod
    def get_repr(cls):
        """Abstract representation of the object for serialization.

        This objects knows how to serialize and deserialize the object and is used by the
        `to_json`, `from_json`, `to_dict` and `from_dict` methods.

        Returns:
            pydantic.BaseModel: The representation of the object.
        """
        try:
            from ..serialization import Serializer
        except ImportError:
            return None
        return Serializer.constructor_repr.get(cls)


class HS3:
    implementation = None

    def __init__(self, obj):
        super().__init__()
        self.obj = obj
        self.original_init = {}

    def to_json(self):
        orm = self.repr.from_orm(self)
        try:
            json_obj = orm.json(exclude_none=True, by_alias=True)
        except TypeError as error:
            if "TypeError: Object of type 'ndarray' is not JSON serializable" in str(
                error
            ):
                raise TypeError(
                    "The object you are trying to serialize contains numpy arrays. "
                    "This is not supported by json. Please use `to_asdf` (or `to_dict)` instead."
                )
            else:
                raise
        return json_obj

    def to_dict(self):
        orm = self.repr.from_orm(self)
        return orm.dict(exclude_none=True, by_alias=True)

    @classmethod
    def from_json(cls, json):
        orm = cls.implementation.get_repr().parse_raw(json)
        return orm.to_orm()

    @property
    def repr(self):
        return self.obj.get_repr()


def create_HS3(cls):
    class HS3Specialized(HS3):
        implementation = cls

    return HS3Specialized
