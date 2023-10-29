from src import MaskGenerator
from src import MapSheet
from src import RectangleMask



with open(r"E:\TU_Delft\Synthesis\iiifmap\project\resources\tmk_neat_combined\8.1.json", "r") as f:
    annotation_content = f.read()

    mapsheet = MapSheet.from_annotationpage(annotation_content)

    mask_generator = MaskGenerator()
    corners = mask_generator.corner_detection(mapsheet)
    mask = RectangleMask.from_corners(*corners)
    mapsheet.set_mask(mask)
    print(mapsheet.to_annotationpage())
    print(corners)
