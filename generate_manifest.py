from IIIFpres import iiifpapi3

def createManifest(base_url, labels, behaviors, canvases):
    iiifpapi3.BASE_URL = base_url
    manifest = iiifpapi3.Manifest()
    manifest.set_id(extendbase_url="manifest.json")
    for label in labels:
        manifest.add_label(label["lang"], label["label"])
    for behavior in behaviors:
        manifest.add_behavior(behavior)
    
    for idx,d in enumerate(canvases):
        idx+=1 
        canvas = manifest.add_canvas_to_items()
        canvas.set_id(extendbase_url="canvas/p%s"%idx) # in this case we use the base url
        canvas.set_height(d[2])
        canvas.set_width(d[1])
        canvas.add_label("en",d[0])
        annopage = canvas.add_annotationpage_to_items()
        annopage.set_id(extendbase_url="page/p%s/1" %idx)
        annotation = annopage.add_annotation_to_items(target=canvas.id)
        annotation.set_id(extendbase_url="annotation/p%s-image"%str(idx).zfill(4))
        annotation.set_motivation("painting")
        annotation.body.set_id("".join(d[3:]))
        annotation.body.set_type("Image")
        annotation.body.set_format("image/jpeg")
        annotation.body.set_width(d[1])
        annotation.body.set_height(d[2])
        s = annotation.body.add_service()
        s.set_id(d[3])
        s.set_type("ImageService3")
        s.set_profile("level1")
    
    return manifest





def test():
    manifest = createManifest(
        base_url="https://iiif.io/api/cookbook/recipe/0009-book-1/",
        labels=[{"lang": "en", "label":"Simple Manifest - Book"}],
        behaviors=["paged"],
        #        label       width height id                                                                            service
        canvases = (("Blank page",3204,4613,"https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f18","/full/max/0/default.jpg"),
                ("Frontispiece",3186,4612,"https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f19","/full/max/0/default.jpg"),
                ("Title page",3204,4613,"https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f20","/full/max/0/default.jpg"),
                ("Blank page",3174,4578,"https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f21","/full/max/0/default.jpg"),
                ("Bookplate",3198,4632,"https://iiif.io/api/image/3.0/example/reference/59d09e6773341f28ea166e9f3c1e674f-gallica_ark_12148_bpt6k1526005v_f22","/full/max/0/default.jpg"),)  
    )
    print(manifest)
    manifest.json_save("test-manifest.json")

if __name__ == '__main__':
    test()