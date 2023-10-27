import json
import os
import logging

from src import MapSheet

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler
file_handler = logging.FileHandler('build_archive_annotations.log', mode='w')
file_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logger.addHandler(console_handler)


NEAT_FOLDER = ["resources", "tmk_neat_combined"]
NEAT_SPLIT_FOLDER = ["resources", "tmk_neat_split"]
FIELD_FOLDER = ["resources", "tmk_field"]
BONNE_FOLDER = ["resources", "bonnebladen"]



def write_annotationpage(mapsheet: MapSheet, folder: list[str]):
    annotationpage = mapsheet.to_annotationpage(indent=4)
    annotationpage_filepath = os.path.join(*folder, mapsheet.id + ".json")
    with open(annotationpage_filepath, "w") as f:
        f.write(annotationpage)

def main():
    tmk_data_path = os.path.join("resources", "tmk_raw_data.json")
    with open(tmk_data_path, "r") as f:
        tmk_data = json.load(f)

    for sheet in tmk_data:
        sheet_title = sheet["title"]
        sheet_index = sheet["sheet"]
        logging.info("Processing TMK sheet '{}'".format(sheet_title))
        nettekeningen = sheet["nettekeningen"]
        if not nettekeningen:
            logging.warning(f"No neat drawings found for sheet {sheet_index} {sheet_title}")
        else:
            combined_neat_mapsheet = mapsheet_from_archive_data(nettekeningen[0], sheet_index, sheet_title)
            write_annotationpage(combined_neat_mapsheet, NEAT_FOLDER)

            if not len(nettekeningen) > 1:
                logging.warning(f"Only one neat drawings found for TMK sheet {sheet_index} {sheet_title}")
            else:
                for split_neat_drawing in nettekeningen[1:]:
                    split_neat_mapsheet = mapsheet_from_archive_data(split_neat_drawing, sheet_index, sheet_title)
                    write_annotationpage(split_neat_mapsheet, NEAT_SPLIT_FOLDER)

        veldminuten = sheet["veldminuten"]
        if not veldminuten:
            logging.warning(f"No field drawings found for sheet {sheet_index} {sheet_title}")
            continue
        for field_minute_data in veldminuten:
            field_minute_mapsheet = mapsheet_from_archive_data(field_minute_data, sheet_index, sheet_title)
            write_annotationpage(field_minute_mapsheet, FIELD_FOLDER)

    bonnebladen_data_path = os.path.join("resources", "bonnebladen_raw_data.json")
    with open(bonnebladen_data_path, "r") as f:
        bonnebladen_data = json.load(f)

    for sheet in bonnebladen_data:
        sheet_title = sheet["title"]
        sheet_index = sheet["sheet"]

        logging.info(f"Processing Bonnebladen sheet: {sheet_index}, {sheet_title}")
        if not sheet["minuten"]:
            logging.warning(f"No field drawings found for Bonnebladen sheet: {sheet_title} ({sheet_index})")
            continue
        for minute in sheet["minuten"]:
            minute_mapsheet = mapsheet_from_archive_data(minute, sheet_index, sheet_title)
            write_annotationpage(minute_mapsheet, BONNE_FOLDER)


def mapsheet_from_archive_data(data, sheet_idx, sheet_title):
    sheet_id = data.get("id")
    image_endpoint = data["images"][0]
    mapsheet = MapSheet(image_endpoint)
    mapsheet.id = sheet_id
    metadata = {
        "date": data["date"],
        "handle": data["handle"],
        "title": sheet_title,
        "sheet": sheet_idx
    }
    mapsheet.metadata = metadata

    return mapsheet


if __name__ == '__main__':
    main()