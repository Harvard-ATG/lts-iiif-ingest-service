import json
import os

import jsonschema
from IIIFpres import iiifpapi3

iiifpapi3.INVALID_URI_CHARACTERS = iiifpapi3.INVALID_URI_CHARACTERS.replace(
    ":", ""
)  # See https://github.com/giacomomarchioro/pyIIIFpres/issues/11


def createManifest(
    base_url: str,
    labels: list,  # of dicts or strings
    canvases: list,
    providers: list = [],
    behaviors: list = ["paged"],
    default_lang: str = "en",
    service_type: str = "ImageService2",  # Image API level - see https://iiif.io/api/presentation/3.0/#service
    service_profile: str = "level2",  # Compliance level - see https://iiif.io/api/image/2.1/compliance/ and https://iiif.io/api/image/3.0/compliance/
    # service_id: str = "https://mps-qa.lib.harvard.edu/assets/images/", # Currently set in annotation.id; used for annotation.body.id and service.id; this is MPS rather than NRS; could be hoisted to here
    manifest_metadata: list = None,
    rights: str = None,
    required_statement: list = None,
    summary: list = None,  # can also be str
    thumbnails: list = None,
) -> iiifpapi3.Manifest():
    """Creates and validates a IIIF manifest"""

    manifest = iiifpapi3.Manifest()
    iiifpapi3.BASE_URL = base_url + "/"
    manifest.set_id(objid=base_url)

    for label in labels:
        if isinstance(label, str):
            manifest.add_label(default_lang, label)
        else:
            manifest.add_label(label.get("lang", default_lang), label["label"])
    for behavior in behaviors:
        manifest.add_behavior(behavior)

    if manifest_metadata:
        for m in manifest_metadata:
            manifest.add_metadata(
                label=m["label"],
                value=m["value"],
                language_l=m.get("label_lang", default_lang),
                language_v=m.get("value_lang", default_lang),
            )

    if rights:
        manifest.set_rights(rights)

    if required_statement:
        for m in required_statement:
            manifest.add_requiredStatement(
                label=m["label"],
                value=m["value"],
                language_l=m.get("label_lang", default_lang),
                language_v=m.get("value_lang", default_lang),
            )

    if providers:
        # https://iiif.io/api/cookbook/recipe/0234-provider/
        # https://github.com/giacomomarchioro/pyIIIFpres/blob/main/examples/0234-provider.py
        # TODO: set more provider fields eg homepage, logo, seeAlso
        for p in providers:
            prov = manifest.add_provider()
            prov.set_id(p.get("id"))
            prov.set_type()
            for label in p["labels"]:
                prov.add_label(
                    language=label.get("lang", default_lang), text=label.get("value")
                )

    if summary:
        if isinstance(summary, str):
            manifest.add_summary(language=default_lang, text=summary)
        else:
            for s in summary:
                manifest.add_summary(
                    language=s.get("lang", default_lang), text=s.get("value")
                )

    if thumbnails:
        for t in thumbnails:
            thum = manifest.add_thumbnail()
            thum.set_id(t.get("id"))
            thum.set_type(t.get("type", "Image"))
            thum.set_format(t.get("format", "image/jpeg"))
            thum.set_height(t.get("height"))
            thum.set_width(t.get("width"))

    for idx, d in enumerate(canvases):
        idx += 1
        canvas = manifest.add_canvas_to_items()
        canvas.set_id(extendbase_url=f"canvas/canvas:{ d.get('asset_id') }")
        canvas.set_height(d["height"])
        canvas.set_width(d["width"])
        if type(d["label"]) is dict:
            canvas.add_label(
                d["label"].get("lang", "default_lang"), d["label"].get("value")
            )
        else:
            canvas.add_label(default_lang, d["label"])
        if "metadata" in d:
            for m in d["metadata"]:
                canvas.add_metadata(
                    label=m["label"],
                    value=m["value"],
                    language_l=m.get("label_lang", default_lang),
                    language_v=m.get("value_lang", default_lang),
                )

        annopage = canvas.add_annotationpage_to_items()
        annopage.set_id(extendbase_url=f"annotationPage/annopage:{d.get('asset_id')}")
        annotation = annopage.add_annotation_to_items(
            target=canvas.id
        )  # TODO: think about handling multiple annotations (images) per canvas
        annotation.set_id(extendbase_url=f"annotation/annotation:{d.get('asset_id')}")
        annotation.set_motivation("painting")
        annotation.body.set_id(f"{d.get('id')}{d.get('service')}")
        annotation.body.set_type("Image")
        annotation.body.set_format(d.get("format"))
        annotation.body.set_width(d.get("width"))
        annotation.body.set_height(d.get("height"))
        s = annotation.body.add_service()
        s.set_id(d.get("id"))
        s.set_type(service_type)
        s.set_profile(service_profile)

    # TODO: Validate the manifest here before returning
    # slightly hacky - pyIIIFpres wants either the objid or extendbase_url to end in "/", but throws an error even if I add extendbase_url="/"
    # we want an ID without the trailing slash, so pass base_url without it; add the "/" manually in line 27; then set manifest.id back to no slash here
    manifest.id = base_url
    return manifest


def validateManifest(manifest: iiifpapi3.Manifest(), read_from_file: bool = True):
    """Validates a manifest. If you pass a string and read_from_file to True, it will read the JSON file to validate"""
    if not os.path.exists('iiif_3_0.json'):
        import urllib.request

        jsonchemadownloadurl = r"https://raw.githubusercontent.com/IIIF/presentation-validator/master/schema/iiif_3_0.json"
        with urllib.request.urlopen(jsonchemadownloadurl) as response, open(
            "iiif_3_0.json", 'wb'
        ) as out_file:
            data = response.read()
            out_file.write(data)
    if read_from_file:
        with open(manifest) as instance, open("iiif_3_0.json") as schema:
            jsonschema.validate(instance=json.load(instance), schema=json.load(schema))
    else:
        with open("iiif_3_0.json") as schema:
            jsonschema.validate(instance=json.load(instance), schema=json.load(schema))


# TODO move tests to an actual tests file, generate test manifests and read in and compare


def cookbook_test():
    manifest = createManifest(
        base_url="https://iiif.io/api/cookbook/recipe/0009-book-1/",
        labels=[{"lang": "en", "label": "Simple Manifest - Book"}],
        canvases=[
            # need to add asset_id for canvas_id
            # need to add format
            {
                "label": "Blank page",
                "width": 3204,
                "height": 4613,
                "id": "https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f18",  # this is really the annotation.id - MPS asset location
                "service": "/full/max/0/default.jpg",
            },
            {
                "label": "Frontispiece",
                "width": 3186,
                "height": 4612,
                "id": "https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f19",
                "service": "/full/max/0/default.jpg",
                "metadata": [
                    {
                        "label": "Reference",
                        "value": "ID124",
                        "label_lang": "en",
                        "value_lang": "en",
                    }
                ],
            },
        ],
        behaviors=["paged"],
        rights="http://creativecommons.org/licenses/by-sa/3.0/",
        required_statement=[
            {
                "label": "Attribution",
                "value": "Cole Crawford",
                "label_lang": "en",
                "value_lang": "en",
            }
        ],
        manifest_metadata=[
            {
                "label": "Creator",
                "value": "Unknown",
                "label_lang": "en",
                "value_lang": "en",
            },
            {
                "label": "Date",
                "value": "19th Century",
                "label_lang": "en",
                "value_lang": "en",
            },
        ],
    )
    manifest.json_save("test-manifest.json")
    return manifest


def mps_mcih_ingest_test():
    manifest = createManifest(
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
    manifest.json_save("ingest-test.json")
    return manifest


if __name__ == '__main__':
    mps_mcih_ingest_test()
