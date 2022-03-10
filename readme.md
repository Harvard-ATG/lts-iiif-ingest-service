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
- Check it was uploaded: `aws s3 ls edu.harvard.huit.lts.mps.at-atdarth-dev` or `aws s3 ls s3://edu.harvard.huit.lts.mps.at-atdarth-dev --recursive --human-readable --summarize`
- Generate a JWT token: `python3 iiif_jwt.py`
- QA MPS endpoint: `https://mps-admin-qa.lib.harvard.edu/admin/ingest/initialize`