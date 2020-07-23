import pathlib
from collections.abc import MutableMapping
from functools import cached_property
from typing import Iterator, Optional

from paquo._base import QuPathBase
from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.java import String, DefaultProjectImageEntry


class _ProjectImageEntryMetadata(MutableMapping):
    """provides a python dict interface for image entry metadata"""

    def __init__(self, entry: DefaultProjectImageEntry) -> None:
        self._entry = entry

    def __setitem__(self, k: str, v: str) -> None:
        if not isinstance(k, str):
            raise ValueError(f"key must be of type `str` got `{type(k)}`")
        if not isinstance(v, str):
            raise ValueError(f"value must be of type `str` got `{type(v)}`")
        self._entry.putMetadataValue(String(str(k)), String(str(v)))

    def __delitem__(self, k: str) -> None:
        if not isinstance(k, str):
            raise ValueError(f"key must be of type `str` got `{type(k)}`")
        self._entry.removeMetadataValue(String(str(k)))

    def __getitem__(self, k: str) -> str:
        if not isinstance(k, str):
            raise ValueError(f"key must be of type `str` got `{type(k)}`")
        v = self._entry.getMetadataValue(String(str(k)))
        if v is None:
            raise KeyError(f"'{k}' not in metadata")
        return str(v)

    def __len__(self) -> int:
        return int(self._entry.getMetadataKeys().size())

    def __iter__(self) -> Iterator[str]:
        return iter(map(str, self._entry.getMetadataKeys()))

    def __contains__(self, item):
        return bool(self._entry.containsMetadata(String(str(item))))

    def clear(self) -> None:
        self._entry.clearMetadata()

    def __repr__(self):
        return f"<Metadata({repr(dict(self))})>"


class QuPathProjectImageEntry(QuPathBase[DefaultProjectImageEntry]):

    def __init__(self, entry: DefaultProjectImageEntry) -> None:
        """Wrapper for qupath image entries

        this is normally not instantiated by the user
        """
        if not isinstance(entry, DefaultProjectImageEntry):
            raise ValueError("don't instantiate directly. use `QuPathProject.add_image`")
        super().__init__(entry)
        self._metadata = _ProjectImageEntryMetadata(entry)
        self._image_data = self.java_object.readImageData()
        if self._image_data is None:
            raise RuntimeError("no image server")

    @property
    def id(self) -> str:
        """the unique image entry id"""
        return str(self.java_object.getID())

    @property
    def image_name(self) -> str:
        """the image entry name"""
        return str(self.java_object.getImageName())

    @image_name.setter
    def image_name(self, name: str) -> None:
        self.java_object.setImageName(String(name))

    @property
    def image_name_original(self) -> Optional[str]:
        """original name in case the user has changed the image name"""
        org_name = self.java_object.getOriginalImageName()
        return str(org_name) if org_name else None

    @property
    def description(self) -> str:
        """free text describing the image"""
        text = self.java_object.getDescription()
        if text is None:
            return ""
        return str(text)

    @description.setter
    def description(self, text: str) -> None:
        self.java_object.setDescription(text)

    @property
    def entry_path(self) -> pathlib.Path:
        """path to the image directory"""
        return pathlib.Path(str(self.java_object.getEntryPath().toString()))

    @property
    def metadata(self) -> _ProjectImageEntryMetadata:
        """the metadata stored on the image as dict-like proxy"""
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict) -> None:
        self._metadata.clear()
        self._metadata.update(value)

    @cached_property
    def hierarchy(self) -> QuPathPathObjectHierarchy:
        """the image entry hierarchy. it contains all annotations"""
        return QuPathPathObjectHierarchy(self._image_data.getHierarchy())

    def __repr__(self):
        return f"<ImageEntry('{self.image_name}')>"

    def save(self):
        """save image entry"""
        if bool(self._image_data.isChanged()):
            self.java_object.saveImageData(self._image_data)
