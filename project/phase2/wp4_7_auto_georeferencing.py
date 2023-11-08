import logging

from src import MapSeries
from src.georeference.matchfinder import get_georeference_from_mapsheet_matches
from logger_config import setup_logging

setup_logging("wp4_7_auto_georeferencing_final_lowres.log")
SHEAR_THRESHOLD = 0.04
SCALE_DIFFERENCE_THRESHOLD = 10
MAX_RETRIES = 3

def validate_georeferencing(georeferencing):
    sheer_factor = georeferencing.shear_factor()
    if abs(sheer_factor) > SHEAR_THRESHOLD:
       logging.warning(f"Sheer factor too high! {sheer_factor}")
       return False
    scale_inaccuracy = georeferencing.scale_inaccuracy(25000, 300)
    if abs(scale_inaccuracy) > SCALE_DIFFERENCE_THRESHOLD:
        logging.warning(f"Scale accuracy too low! Map scale {round(scale_inaccuracy)}% different "
                        f"from georeferencing result.")
        return False

    logging.info(f"Automatic georeferencing within thresholds. "
                 f"Scale inaccuracy: {round(scale_inaccuracy)}% and shear factor: {sheer_factor:2f}.")
    return True

def main():
    fieldminute_series = MapSeries.from_annotationpage_folder(
        "/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/project/resources/tmk_field")
    neatdrawings_series = MapSeries.from_annotationpage_folder(
        "/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/project/phase1/results_wp3/tmk_neat_combined")

    total_sheets = len(fieldminute_series.mapsheets)
    succesful_sheets = 0
    total_retries = 0
    logging.info(f"Georeferencing {total_sheets} TMK veldminuten sheets.")

    for sheet in fieldminute_series.mapsheets:
        logging.info("Starting sheet {}".format(sheet.id))

        try:
            sheet_idx = sheet.metadata["sheet"]

            neatdrawing = next(nsheet for nsheet in neatdrawings_series.mapsheets if nsheet.metadata["sheet"] == sheet_idx)

            georeferencing = get_georeference_from_mapsheet_matches(sheet, neatdrawing)
            #georeferencing = get_georeference_from_mapsheet_template_matching(sheet, 25000, neatdrawing, 50000)

            succesful = validate_georeferencing(georeferencing)
            retries = 0
            failed = False
            while not succesful:
                retries += 1
                if retries >= MAX_RETRIES:
                    logging.error("Reached maximum retries. Sheet has not been georeferenced.") # TODO template matching
                    failed = True
                    break
                logging.info(f"Retry {retries}/{MAX_RETRIES}...")
                georeferencing = get_georeference_from_mapsheet_matches(sheet, neatdrawing)
                succesful = validate_georeferencing(georeferencing)
                sheet.set_georeference(georeferencing)
                fn = f"retries_final/{sheet.id}_{retries}.json"
                with open(fn, "w") as f:
                    logging.debug(f"Wrote: {fn}")
                    f.write(sheet.to_annotationpage())
            if failed:
                continue

            sheet.set_georeference(georeferencing)
            succesful_sheets += 1
            total_retries += retries

            fn = f"results_final/{sheet.id}.json"
            with open(fn, "w") as f:
                logging.debug(f"Wrote: {fn}")
                f.write(sheet.to_annotationpage())
        except Exception as e:
            logging.critical(e)


    with open("full_tmk_minutes_final.json", "w") as f:
        f.write(fieldminute_series.to_annotationpage())

    logging.info(f"Successfully georeferenced {succesful_sheets}/{total_sheets} sheets. "
                 f"Average retry rate: {total_retries/succesful_sheets}")


if __name__ == "__main__":
    main()