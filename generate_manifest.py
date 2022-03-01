from IIIFpres import iiifpapi3
import os
import jsonschema
import json

def createManifest(
    base_url: str,
    labels: list, 
    canvases: list,
    behaviors: list = ["paged"],
    manifestMetadata: list = None,
    rights: str = None,
    required_statement: list = None
) -> iiifpapi3.Manifest():
    """ Creates and validates a IIIF manifest """
    iiifpapi3.BASE_URL = base_url
    manifest = iiifpapi3.Manifest()
    manifest.set_id(extendbase_url="manifest.json")
    for label in labels:
        manifest.add_label(label["lang"], label["label"])
    for behavior in behaviors:
        manifest.add_behavior(behavior)
    
    if(manifestMetadata):
        for m in manifestMetadata:
            manifest.add_metadata(
                label=m["label"],
                value=m["value"],
                language_l=m["label_lang"],
                language_v=m["value_lang"]
            )
    
    if(rights):
        manifest.set_rights(rights)
    
    if(required_statement):
        for m in required_statement:
            manifest.add_requiredStatement(
                label=m["label"],
                value=m["value"],
                language_l=m["label_lang"],
                language_v=m["value_lang"]
            )
    
    for idx,d in enumerate(canvases):
        idx+=1 
        canvas = manifest.add_canvas_to_items()
        canvas.set_id(extendbase_url="canvas/p%s"%idx) # in this case we use the base url
        canvas.set_height(d["height"])
        canvas.set_width(d["width"])
        canvas.add_label("en",d["label"])
        if "metadata" in d:
            for m in d["metadata"]:
                canvas.add_metadata(
                    label=m["label"],
                    value=m["value"],
                    language_l=m["label_lang"],
                    language_v=m["value_lang"]
                )

        annopage = canvas.add_annotationpage_to_items()
        annopage.set_id(extendbase_url="page/p%s/1" %idx)
        annotation = annopage.add_annotation_to_items(target=canvas.id)
        annotation.set_id(extendbase_url="annotation/p%s-image"%str(idx).zfill(4))
        annotation.set_motivation("painting")
        annotation.body.set_id(f"{d['id']}{d['service']}")
        annotation.body.set_type("Image")
        annotation.body.set_format("image/jpeg")
        annotation.body.set_width(d["width"])
        annotation.body.set_height(d["height"])
        s = annotation.body.add_service()
        s.set_id(d["id"])
        s.set_type("ImageService3")
        s.set_profile("level1")
    
    # Validate the manifest here before returning
    return manifest


def validateManifest(manifest: iiifpapi3.Manifest(), read_from_file: bool = True):
    """Validates a manifest. If you pass a string and read_from_file to True, it will read the JSON file to validate"""
    if not os.path.exists('iiif_3_0.json'):
        import urllib.request
        jsonchemadownloadurl = r"https://raw.githubusercontent.com/IIIF/presentation-validator/master/schema/iiif_3_0.json"
        with urllib.request.urlopen(jsonchemadownloadurl) as response, open("iiif_3_0.json", 'wb') as out_file:
            data = response.read()
            out_file.write(data)
    if read_from_file:
        with open(manifest) as instance, open("iiif_3_0.json") as schema:
            jsonschema.validate(instance=json.load(instance),schema=json.load(schema))
    else:
        with open("iiif_3_0.json") as schema:
            jsonschema.validate(instance=json.load(instance),schema=json.load(schema))


def test():
    manifest = createManifest(
        base_url="https://iiif.io/api/cookbook/recipe/0009-book-1/",
        labels=[{"lang": "en", "label":"Simple Manifest - Book"}],
        #        label       width height id                                                                            service
        canvases = [
            { "label": "Blank page", "width": 3204, "height": 4613, "id": "https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f18", "service": "/full/max/0/default.jpg" },
            { "label": "Frontispiece", "width": 3186, "height": 4612, "id": "https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f19", "service":"/full/max/0/default.jpg",
                "metadata": [
                    {
                        "label": "Reference",
                        "value": "ID124",
                        "label_lang": "en",
                        "value_lang": "en"
                    }
                ]
             }
        ],
        behaviors=["paged"],
        rights = "http://creativecommons.org/licenses/by-sa/3.0/",
        required_statement=[
            {
                "label": "Attribution",
                "value": "Cole Crawford",
                "label_lang": "en",
                "value_lang": "en"
            }
        ],
        manifestMetadata=[
            {
                "label": "Creator",
                "value": "Unknown",
                "label_lang": "en",
                "value_lang": "en"
            },
            {
                "label": "Date",
                "value": "19th Century",
                "label_lang": "en",
                "value_lang": "en"
            }
        ]
    )
    manifest.json_save("test-manifest.json")
    return manifest

if __name__ == '__main__':
    test()