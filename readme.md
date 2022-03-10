# IIIF LTS Library
This will be a Python library to interact with the LTS media ingest solution. Functionality to include JWT token generation, interacting with buckets, etc.

## Resources
- [Authentication & Authorization](https://docs.google.com/document/d/1qKHD--VUCWH4aEXUv7E3jEf0AnLDgNyhMpSLqCqnLbY/edit#heading=h.uuca9t2f0d35)
- [Ingest API](https://docs.google.com/document/d/1seTnNx8Unwl4w4n39rdUKESuxU1IWMlpLjpZMVbsA1U/edit#heading=h.ru4gjiray64u)

## Auth
Currently store tokens in /auth which is ignored. Think about better ways to handle this.
File hierarchy: 
- auth
    - dev
        - issuers
            - atmch.json
            - atmediamanager.json
            - atomeka.json
        - keys
            - atmch
                - atmcihdefault
                    - private.key
                    - public.key 
            - atmediamanager
                - atmediamanagerdefault
                    - private.key
                    - public.key
            - atomeka
                - atomeka
                    - private.key
                    - public.key
    - prod
        ...
    - qa
        ...


## Examples and notes
- Upload a file: `python3 bucket.py --file=/Users/colecrawford/Github/lts-iiif-ingest-service/test_images/27.586.1-cm-2016-02-09.tif --bucket=edu.harvard.huit.lts.mps.at-atdarth-dev`
- Check it was uploaded: `aws s3 ls edu.harvard.huit.lts.mps.at-atdarth-dev`
- Generate a JWT token: `python3 iiif_jwt.py`
- QA MPS endpoint: `https://mps-admin-qa.lib.harvard.edu/admin/ingest/initialize`


## Ingesting images and simple V2 manifest via Postman and without manifest generation(iiifpres module)
Prerequisite if you are using `aws cli`, you must set `export AWS_PROFILE=<BUCKET CREDENTIALS>` to your desired bucket corresponding to your `.aws/credentials` permissions to upload files
- Upload a file using `bucket.py` via [Examples and notes](#examples-and-notes) or the command below: 
```
$ export IIIF_QA_BUCKET=edu.harvard.huit.lts.mps.at-atomeka-qa
$ aws s3 cp ./test_images/27.586.2A-cm-2016-02-09.tif s3://$IIIF_QA_BUCKET/iiif/
```

Note: you will need to set/create the folder/path inside the bucket named `/iiif/`

- Generate the jwt token via [Examples and notes](#examples-and-notes). You will need to have the correct `private.key` and `public.key` in similar folder structure `/auth/qa/keys/omeka/omekadefault` and modify the test function within `iiif_jwt.py` to the following parameters `load_auth("atomeka", "qa")`

- Create the ingess json using the example provided in `sample-manifests/success-test-ingest-manifest.json`. There is an example below with some fields ommited. You will need to update the fields listed below with `<UNIQUE IDENTIFIER>`(example: `OMEKATEST2`) and `<UNIQUE ID or NAME>`(corresponds with `URN-3` @id, example: `OMEKAMANIFEST2`) in your own json file.
```
{ ...
    "assets": {
      ...
      "image": [
        {
          ...
          "storageSrcKey": <Name of the image e.g."27.586.2A-cm-2016-02-09.tif">,
          "identifier":"AT:<UNIQUE IDENTIFIER>",
         ...
    },
     "manifest" : {
      "@context": "http://iiif.io/api/presentation/2/context.json",
      "@id": "https://mps-qa.lib.harvard.edu/iiif/2/URN-3:AT:<UNIQUE ID or NAME>:MANIFEST:2",
      ...
      ,
      "sequences": [
              {
                  "@id": "https://mps-qa.lib.harvard.edu/URN-3:AT:<UNIQUE ID or NAME>/...
                  "canvases": [
                      {
                          "@id": "https://mps-qa.lib.harvard.edu/URN-3:AT:<UNIQUE ID or NAME>/canvas/canvas-400000206.json",
                        ...
                          "images": [
                              {
                                  "@id": "https://mps-qa.lib.harvard.edu/URN-3:AT:<UNIQUE ID or NAME>/annotation/annotation-400000206.json",
                                 ...
                                  "on": "https://mps-qa.lib.harvard.edu/URN-3:AT:<UNIQUE ID or NAME>/canvas/canvas-400000206.json",
                                  "resource": {
                                      "@id": "https://mps-qa.lib.harvard.edu/assets/images/AT:<UNIQUE IDENTIFIER>/full/full/0/default.jpg",
                                      ...
                                      "service": {
                                         ...
                                          "@id": "https://mps-qa.lib.harvard.edu/assets/images/AT:<UNIQUE IDENTIFIER>"
                                      }
                                  }
                              }
                          ],
                          "thumbnail": {
                              "@id": "https://mps-qa.lib.harvard.edu/assets/images/AT:<UNIQUE IDENTIFIER>/full/,100/0/default.jpg",
                              "@type": "dctypes:Image"
                          }
                      }
                  ]
              }
          ],
          "structures": [
              {
                  "@id": "https://mps-qa.lib.harvard.edu/URN-3:AT:<UNIQUE ID or NAME>/range/range-0-0.json",
                  ...
                  "canvases": ["https://mps-qa.lib.harvard.edu/URN-3:AT:<UNIQUE ID or NAME>/canvas/canvas-400000206.json"]
              }
          ]
      }
}
```
- use Postman to first set the bearer token to the generated jwt from previous steps and `POST` the json that you modified to the following endpoint: `https://mps-admin-qa.lib.harvard.edu/admin/ingest/initialize` Note: you will need to be on the `#WEBS` VPN for the `POST` to work.
- After recieving a `200 success code` you should be able to access the image via `https://mps-qa.lib.harvard.edu/assets/images/AT:<UNIQUE IDENTIFIER>/full/,100/0/default.jpg` and manifest via `https://mps-qa.lib.harvard.edu/iiif/c/URN-3:AT:<UNIQUE ID or NAME>`