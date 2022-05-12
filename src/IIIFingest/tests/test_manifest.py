import pytest  # noqa: F401
from IIIFpres.utilities import read_API3_json

from ..generate_manifest import createManifest, validateManifest  # noqa: F401

# Given a IIIF cookbook manifest, generate and it matches the known cookbook
# def test_iiif_cookbook_manifest():
#     manifest = createManifest(
#         base_url="https://iiif.io/api/cookbook/recipe/0009-book-1/",
#         labels=[{"lang": "en", "label": "Simple Manifest - Book"}],
#         canvases=[
#             # need to add asset_id for canvas_id
#             # need to add format
#             {
#                 "label": "Blank page",
#                 "width": 3204,
#                 "height": 4613,
#                 "id": "https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f18",  # this is really the annotation.id - MPS asset location
#                 "service": "/full/max/0/default.jpg",
#             },
#             {
#                 "label": "Frontispiece",
#                 "width": 3186,
#                 "height": 4612,
#                 "id": "https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f19",
#                 "service": "/full/max/0/default.jpg",
#                 "metadata": [
#                     {
#                         "label": "Reference",
#                         "value": "ID124",
#                         "label_lang": "en",
#                         "value_lang": "en",
#                     }
#                 ],
#             },
#         ],
#         behaviors=["paged"],
#         rights="http://creativecommons.org/licenses/by-sa/3.0/",
#         required_statement=[
#             {
#                 "label": "Attribution",
#                 "value": "Cole Crawford",
#                 "label_lang": "en",
#                 "value_lang": "en",
#             }
#         ],
#         manifest_metadata=[
#             {
#                 "label": "Creator",
#                 "value": "Unknown",
#                 "label_lang": "en",
#                 "value_lang": "en",
#             },
#             {
#                 "label": "Date",
#                 "value": "19th Century",
#                 "label_lang": "en",
#                 "value_lang": "en",
#             },
#         ],
#     )
#     manifest.json_save("test-manifest.json")
#     return manifest


# Given ingest params, generate a manifest and it matches an existing known good manifest
def test_mps_mcih_manifest_creation():
    test_manifest = createManifest(
        base_url="https://nrs-qa.lib.harvard.edu/URN-3:AT:TESTMANIFEST3:MANIFEST:3",
        labels=[{"lang": "en", "label": "Test DARTH manifest - Cole"}],
        required_statement=[
            {
                "label": "Attribution",
                "value": "Jinah Kim",
                "label_lang": "en",
                "value_lang": "en",
            }
        ],
        canvases=[
            {
                "label": "Test image 1",  # this can be a string, which uses the default_lang, or a dict with lang/value
                "height": 564,
                "width": 3600,
                "asset_id": "TESTASSET3",  # canvas.id
                "id": "https://mps-qa.lib.harvard.edu/assets/images/AT:TESTASSET3",  # service.id
                "service": "/full/max/0/default.tif",  # anno.id = service.id + service; should have a default service based on format
                "format": "image/tiff",  # could get this from the filepath
                "metadata": [],
            },
            {
                "label": "Test image 2",
                "height": 581,
                "width": 3600,
                "asset_id": "TESTASSET4",
                "id": "https://mps-qa.lib.harvard.edu/assets/images/AT:TESTASSET4",
                "service": "/full/max/0/default.tif",
                "format": "image/tiff",
                "metadata": [],
            },
        ],
        rights="http://creativecommons.org/licenses/by-sa/3.0/",
        manifest_metadata=[
            {
                "label": "Creator",
                "value": "Unknown",
                "label_lang": "en",
                "value_lang": "en",
            }
        ],
    )

    # with open("manifests/ingest-test.json") as f:
    #     canonical_manifest = json.load(f)
    canonical_manifest = read_API3_json('manifests/ingest-test.json')
    print(test_manifest)
    print(canonical_manifest)
    assert test_manifest == canonical_manifest


# Validate a manifest
