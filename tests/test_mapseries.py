import pytest

from src import MapSeries

@pytest.mark.skip
def test_open_allmaps(sample_mapseries):
    sample_mapseries.open_in_allmaps()

def test_series_from_folder():
    folder = "project/resources/tmk_neat_combined"
    series = MapSeries.from_annotationpage_folder(folder)
    assert series.mapsheets
    assert series.mapsheets[0].metadata["title"] == "Ameland"