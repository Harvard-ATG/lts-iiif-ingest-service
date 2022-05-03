import pytest
import os.path
from PIL import Image

from ..asset import get_image_size


def test_get_image_size():
    abs_path = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(abs_path, "images", "27.586.1-cm-2016-02-09.tif")
    w, h = get_image_size(image_path)
    # assert (w, h) == (3600, 1)
    assert w == 3600
    assert h == 564



