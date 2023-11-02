import json
import os
import urllib.parse
import webbrowser

import logging
from . import MapSheet

def _get_recursive_filenames(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for fn in files:
            yield root, fn

def _get_nonrecursive_filenames(folder_path):
    for fn in os.listdir(folder_path):
        yield folder_path, fn

class MapSeries:
    mapsheets: list["MapSheet"]
    _manifest: str

    def __init__(self):
        self.mapsheets = []

    def from_iiif_endpoints(self, endpoints: list[str]):
        raise NotImplementedError
        pass

    @classmethod
    def from_manifest(cls, manifest: str) -> "MapSeries":
        raise NotImplementedError
        self = cls()
        self._manifest = manifest
        json_data = json.loads(manifest)
        for item in json_data["items"]:
            endpoint = item["target"]["service"][0]["@id"]
            self.mapsheets.append(MapSheet("test", endpoint))

        return self

    @classmethod
    def from_annotationpage_folder(cls, folder_path: str, recursive: bool = True) -> "MapSeries":
        if recursive:
            files = _get_recursive_filenames(folder_path)
        else:
            files = _get_nonrecursive_filenames(folder_path)

        self = cls()
        for root, fn in files:

            if not fn.endswith(".json"):
                logging.debug(f"Skipping file {fn}")
                continue

            fp = os.path.join(root, fn)
            with open(fp, "r") as f:
                logging.debug(f"Adding annotationpage {fn} to mapseries.")
                content = f.read()

            sheet = MapSheet.from_annotationpage(content)
            self.mapsheets.append(sheet)

        return self

    @classmethod
    def from_annotationpage(cls, annotationpage: str) -> "MapSeries":
        self = cls()
        annotations = json.loads(annotationpage)["items"]
        for annotation in annotations:
            self.mapsheets.append(MapSheet.from_annotation(annotation))

        return self

    def to_annotationpage(self, indent=4) -> str:
        annotations = []
        for sheet in self.mapsheets:
            if not sheet._georeference:
                logging.warning(f"Could not export sheet {sheet.id} to annotationpage because it's missing a georeference.")
                continue
            annotations.append(sheet.to_annotation())

        annotationpage = {
            "type": "AnnotationPage",
            "@context": [
                "http://www.w3.org/ns/anno.jsonld"
            ],
            "items": annotations
        }

        return json.dumps(annotationpage, indent=indent)

    def open_in_allmaps(self):
        serialized_json = urllib.parse.quote(self.to_annotationpage())
        url = "https://viewer.allmaps.org/#data=" + serialized_json
        webbrowser.open(url)
