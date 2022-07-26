import mimetypes
import os.path

import pytest

from IIIFingest.asset import Asset, create_asset_id, get_filename_noext, get_image_size


def test_get_image_size(test_images):
    test_image = test_images["mcihtest1.tif"]
    actual_width, actual_height = get_image_size(test_image["filepath"])

    assert actual_width == test_image["width"]
    assert actual_height == test_image["height"]


def test_get_filename_noext(test_images):
    test_image = test_images["mcihtest1.tif"]
    expected = os.path.basename(os.path.splitext(test_image["filename"])[0])
    actual = get_filename_noext(test_image["filepath"])

    assert actual == expected


def test_create_asset_id_without_uuid():
    asset_prefix = "myapp"
    identifier = "1001"
    asset_id = create_asset_id(
        asset_prefix=asset_prefix,
        identifier=identifier,
        with_uuid=False,
    )

    assert asset_id == f"{asset_prefix}{identifier}"


def test_create_asset_id_with_uuid():
    asset_prefix = "myapp"
    identifier = "1002"
    asset_id = create_asset_id(
        asset_prefix=asset_prefix,
        identifier=identifier,
        with_uuid=True,
    )

    expected_start = f"{asset_prefix}{identifier}"
    expected_uuid_size = 22

    actual_start = asset_id[:-expected_uuid_size]
    actual_uuid = asset_id[len(expected_start) :]

    assert actual_start == expected_start
    assert len(actual_uuid) == expected_uuid_size


@pytest.mark.parametrize(
    "invalid_asset_id", ["myapp:123", "myapp/123", "myapp-123", "myapp_123"]
)
def test_create_asset_invalid_asset_id(invalid_asset_id):
    with pytest.raises(ValueError):
        Asset(asset_id=invalid_asset_id)


def test_create_asset_with_no_asset_id():
    asset = Asset(asset_id=None)
    assert asset.asset_id is None


def test_create_asset_from_file(test_images):
    test_image = test_images["mcihtest1.tif"]
    image_path = test_image["filepath"]
    width = test_image["width"]
    height = test_image["height"]
    format = test_image["format"]
    extension = mimetypes.guess_extension(test_image["format"])
    label = "Test Image"
    metadata = [{"label": "Test", "value": "Image level metadata"}]
    asset_id = "myapp1234"

    asset = Asset.from_file(
        image_path,
        asset_id=asset_id,
        label=label,
        metadata=metadata,
    )

    assert asset.asset_id == asset_id
    assert asset.filepath == image_path
    assert asset.format == format
    assert asset.extension == extension
    assert asset.label == label
    assert asset.metadata == metadata
    assert asset.width == width
    assert asset.height == height


def test_asset_upload(test_images, mocker):
    test_image = test_images["mcihtest1.tif"]
    image_path = test_image["filepath"]
    filename = test_image["filename"]
    s3_path = "img/"
    expected_s3_key = f"{s3_path}{filename}"

    mocker.patch(
        'IIIFingest.asset.upload_image_by_filepath', return_value=expected_s3_key
    )

    asset = Asset.from_file(image_path, asset_id="myapp1234")
    actual_s3_key = asset.upload(bucket_name="ingestbucket", s3_path=s3_path)

    assert actual_s3_key == expected_s3_key
