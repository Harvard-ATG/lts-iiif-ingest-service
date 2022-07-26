import mimetypes
import os
import magic
from typing import Optional, Union, BinaryIO, TextIO

import shortuuid
from PIL import Image

from .bucket import upload_image_by_filepath, upload_image_by_fileobj


def get_image_size(
    file: Union[str, BinaryIO, TextIO]
) -> tuple:
    """
    Get the image size for a given file. File can be a file path or a file-like
    object. Returns a tuple with width and height.
    """
    with Image.open(file) as img:
        w, h = img.size
        return w, h


def get_filename_noext(filepath):
    path_root = os.path.splitext(filepath)[0]
    return os.path.basename(path_root)


def create_asset_id(
    asset_prefix: str = "",
    identifier: str = "",
    with_uuid: bool = True,
):
    identifier = identifier if identifier else ""
    optional_uuid = shortuuid.uuid() if with_uuid else ""
    return f"{asset_prefix}{identifier}{optional_uuid}"


class Asset:
    """
    Constructs an Asset to be ingested.
    """

    def __init__(
        self,
        asset_id=None,
        fileobj=None,
        filepath=None,
        s3key=None,
        format=None,
        extension=None,
        width=None,
        height=None,
        label=None,
        metadata=None,
    ):
        if asset_id and not asset_id.isalnum():
            raise ValueError(
                f"Invalid asset_id {asset_id} - must be alphanumeric only."
            )

        self.asset_id = asset_id
        self.fileobj = fileobj
        self.filepath = filepath
        self.s3key = s3key
        self.format = format
        self.extension = extension
        self.width = width
        self.height = height
        self.label = label if label else ""
        self.metadata = metadata if metadata else {}

    def upload(
        self,
        bucket_name: str = "",
        s3_path: Optional[str] = None,
        boto_session=None
    ) -> str:
        """
        Uploads the asset to the designated bucket. Chooses a strategy based on
        whether the asset has a filepath or a fileobj.
        """
        if self.filepath:
            self.s3key = upload_image_by_filepath(
                filepath=self.filepath,
                bucket_name=bucket_name,
                s3_path=s3_path,
                session=boto_session,
            )
        elif self.fileobj:
            self.s3key = upload_image_by_fileobj(
                fileobj=self.fileobj,
                filename=self.label,
                bucket_name=bucket_name,
                s3_path=s3_path,
                session=boto_session,
            )
        else:
            raise NameError("Asset has neither filepath or fileobj: {self}")
        return self.s3key

    @classmethod
    def from_file(cls, filepath, **kwargs):
        """
        Constructs an Asset from a file.
        """
        asset_id = kwargs.get("asset_id")

        if kwargs.get("width") and kwargs.get("height"):
            width = kwargs["width"]
            height = kwargs["height"]
        else:
            width, height = get_image_size(filepath)

        if kwargs.get("format"):
            format = kwargs.get("format")
        else:
            format, encoding = mimetypes.guess_type(filepath)

        if kwargs.get("extension"):
            extension = kwargs.get("extension")
        else:
            extension = mimetypes.guess_extension(format) or ""

        if kwargs.get("label"):
            label = kwargs.get("label")
        else:
            label = asset_id

        metadata = kwargs.get("metadata", {})

        return cls(
            filepath=filepath,
            asset_id=asset_id,
            format=format,
            extension=extension,
            width=width,
            height=height,
            label=label,
            metadata=metadata,
        )

    @classmethod
    def from_fileobj(cls, fileobj, **kwargs):
        """
        Constructs an Asset from a file.
        """
        asset_id = kwargs.get("asset_id")

        if kwargs.get("width") and kwargs.get("height"):
            width = kwargs["width"]
            height = kwargs["height"]
        else:
            width, height = get_image_size(fileobj)

        if kwargs.get("format"):
            format = kwargs.get("format")
        elif hasattr(fileobj, 'content_type'):
            # Django UploadedFile objects have a content type attribute
            # that can be used here
            format = fileobj.content_type
        else:
            format = magic.from_buffer(fileobj, mime=True)

        if kwargs.get("extension"):
            extension = kwargs.get("extension")
        else:
            extension = mimetypes.guess_extension(format) or ""

        if kwargs.get("label"):
            label = kwargs.get("label")
        else:
            label = asset_id

        metadata = kwargs.get("metadata", {})

        return cls(
            fileobj=fileobj,
            asset_id=asset_id,
            format=format,
            extension=extension,
            width=width,
            height=height,
            label=label,
            metadata=metadata,
        )

    def to_dict(self):
        """
        Returns a dict representation of the Asset.
        """
        return {
            "asset_id": self.asset_id,
            "filepath": self.filepath,
            "fileobj": self.fileobj,
            "s3key": self.s3key,
            "format": self.format,
            "extension": self.extension,
            "width": self.width,
            "height": self.height,
            "label": self.label,
            "metadata": self.metadata,
        }

    def __str__(self):
        return "Asset: " + str(sorted(self.to_dict().items()))
