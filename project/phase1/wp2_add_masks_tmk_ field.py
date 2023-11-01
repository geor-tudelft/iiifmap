import os
from src import MaskGenerator
from src import MapSheet
from src import RectangleMask


report_path = r"E:\TU_Delft\Synthesis\iiifmap\project\phase1\results_wp2\tmk_field\report.txt"  # path to save the report
directory = r"E:\TU_Delft\Synthesis\iiifmap\project\resources\tmk_field"  # path with map sheets
files_names = os.listdir(directory)
total = len(files_names)
i = 0 # Counter for progress
for file_name in files_names:
    file = os.path.join(directory, file_name)
    # print(file)
    i += 1
    print(round((i/total)*100, 2))
    with open(file, "r") as f:
        annotation_content = f.read()

        mapsheet = MapSheet.from_annotationpage(annotation_content)
        mask_generator = MaskGenerator()
        try:
            corners = mask_generator.background_removal(mapsheet, plot=False)
            mask = RectangleMask.from_corners(*corners)
            mapsheet.set_mask(mask)
            with open(rf"E:\TU_Delft\Synthesis\iiifmap\project\phase1\results_wp2\tmk_field\{file_name}", 'w') as ap:  # path to write the updated annotation pages
                ap.write(mapsheet.to_annotationpage())
        except:
            with open(report_path, "a") as report:
                report.write(f"{file_name}\n")
            print(f"Could not find mask for {file_name}")
            continue
	"""
    If the user uses Plot function from corner_detection() 
    it is recommended to uncomment the following section
    """
    # user_input = input("Enter to continue or q to quit:")
    # if user_input == "q":
    #     break
