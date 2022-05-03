import pytest
import os.path
from PIL import Image

from ..asset import get_image_size, Asset

def broken_asset_id():
    return Asset(asset_id="test-ing")

def test_get_image_size():
    abs_path = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(abs_path, "images", "27.586.1-cm-2016-02-09.tif")
    w, h = get_image_size(image_path)
    # assert (w, h) == (3600, 1)
    assert w == 3600
    assert h == 564

def test_asset_raises_value_error():
    with pytest.raises(ValueError):
        broken_asset_id()

