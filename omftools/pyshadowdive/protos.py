import json
import typing
from enum import Enum
from abc import ABCMeta
from validx import exc, Dict, Validator

from .utils.parser import BinaryParser
from .utils.exceptions import OMFInvalidDataException

PropertyDict = typing.List[
    typing.Tuple[
        str,
        typing.Union[str, float, int],
        typing.Union[str, float, int, None],
    ]]


class DataObject(metaclass=ABCMeta):
    __slots__ = ()

    def read(self, parser: BinaryParser) -> 'DataObject':
        raise NotImplementedError()

    def write(self, parser: BinaryParser) -> None:
        raise NotImplementedError()

    def unserialize(self, data: dict) -> 'DataObject':
        raise NotImplementedError()

    def serialize(self) -> dict:
        raise NotImplementedError()

    def get_props(self) -> PropertyDict:
        content: PropertyDict = []
        for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
            for attr in slots:
                var = getattr(self, attr, None)
                if type(var) in [float, int, str] or issubclass(type(var), Enum):
                    dec_var = getattr(self, f'real_{attr}', None)
                    content.append((attr, var, dec_var))
        return content


class Entrypoint(DataObject):
    __slots__ = ()

    schema: Validator = Dict()

    def load_native(self, filename: str) -> 'Entrypoint':
        with open(filename, 'rb', buffering=8192) as handle:
            self.read(BinaryParser(handle))
        return self

    def save_native(self, filename: str) -> None:
        with open(filename, 'wb', buffering=8192) as handle:
            self.write(BinaryParser(handle))

    def load_json(self, filename: str) -> 'Entrypoint':
        with open(filename, 'rb', buffering=8192) as handle:
            self.from_json(handle.read().decode())
        return self

    def save_json(self, filename: str, **kwargs) -> None:
        with open(filename, 'wb', buffering=8192) as handle:
            handle.write(self.to_json(**kwargs).encode())

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.serialize(), **kwargs)

    def from_json(self, data: str) -> 'Entrypoint':
        decoded_data = json.loads(data)

        try:
            self.schema(decoded_data)
        except exc.ValidationError as e:
            e.sort()
            rows = [f"{c}: {m}" for c, m in exc.format_error(e)]
            raise OMFInvalidDataException('\n'.join(rows))

        return self.unserialize(decoded_data)
