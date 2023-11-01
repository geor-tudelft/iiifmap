from ..custom_types import Cv2Image, PixelCoordinate
from .baseclass import Mask, RectangleMask

from PIL import Image
import cv2 as cv
import numpy as np
import math


class MaskGenerator:
    maximum_corner_count: int
    resolution: 'Resolution'


    def from_mapsheet(self, sheet_image: Cv2Image) -> Mask:
        ...

    def corner_detection(self, map_sheet: 'MapSheet', plot=False) -> list[PixelCoordinate]:
        from src.mapsheet import MapSheet, Resolution
        image_or = map_sheet.get_image(resolution=Resolution.MAX)

        image = image_or[150:image_or.shape[0] - 150, 150:image_or.shape[1] - 150]
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        gray = cv.bitwise_not(image)
        bw = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 21, -2)

        horizontal = np.copy(bw)
        vertical = np.copy(bw)

        # Create structure element for extracting horizontal lines through morphology operations
        horizontalStructure = cv.getStructuringElement(cv.MORPH_RECT, (21, 1), (-1, -1))
        # Apply morphology operations
        horizontal = cv.erode(horizontal, horizontalStructure)
        horizontal = cv.dilate(horizontal, horizontalStructure)

        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv.getStructuringElement(cv.MORPH_RECT, (1, 15))
        # Apply morphology operations
        vertical = cv.erode(vertical, verticalStructure)
        vertical = cv.dilate(vertical, verticalStructure)

        # Line detection from structures
        linesP_horizontal = cv.HoughLinesP(horizontal, 1, np.pi / 180, 200, None, 250, 20)
        linesP_vertical = cv.HoughLinesP(vertical, 1, np.pi / 180, 200, None, 250, 20)

        # Filter lines that are not horizontal or vertical
        horizontal_filtered = []
        vertical_filtered = []

        for i in range(0, len(linesP_horizontal)):
            angle = math.atan2(linesP_horizontal[i][0][3] - linesP_horizontal[i][0][1],
                               linesP_horizontal[i][0][2] - linesP_horizontal[i][0][0]) * 180 / math.pi
            if math.isclose(angle, 0, abs_tol=4):
                horizontal_filtered.append(linesP_horizontal[i])
                # print("Horizontal angle:", angle)
        for j in range(0, len(linesP_vertical)):
            angle = math.atan2(linesP_vertical[j][0][3] - linesP_vertical[j][0][1],
                               linesP_vertical[j][0][2] - linesP_vertical[j][0][0]) * 180 / math.pi
            if math.isclose(angle, 90, abs_tol=4) or math.isclose(angle, -90, abs_tol=4):
                vertical_filtered.append(linesP_vertical[j])
                # print("Vertical angle:", angle)

        # Create blank images
        horizontal_blank = np.zeros(image.shape, image.dtype)
        vertical_blank = np.zeros(image.shape, image.dtype)

        # Draw filtered lines on blank images
        for i in range(0, len(horizontal_filtered)):
            cv.line(horizontal_blank, (horizontal_filtered[i][0][0], horizontal_filtered[i][0][1]),
                    (horizontal_filtered[i][0][2], horizontal_filtered[i][0][3]),
                    (255, 255, 255), 1, cv.LINE_AA)
        for j in range(0, len(vertical_filtered)):
            cv.line(vertical_blank, (vertical_filtered[j][0][0], vertical_filtered[j][0][1]),
                    (vertical_filtered[j][0][2], vertical_filtered[j][0][3]),
                    (255, 255, 255), 1, cv.LINE_AA)

        # Get index of horizontal and vertical lines that are closest to the edges of the image
        h = image.shape[0]
        w = image.shape[1]
        indexVerticalL = 0
        indexVerticalR = 0
        x = w / 2
        x2 = w / 2
        for i in range(0, len(vertical_filtered)):
            if x >= vertical_filtered[i][0][0] > 0:
                indexVerticalL = i
                x = vertical_filtered[i][0][0]
            elif image.shape[1]> vertical_filtered[i][0][0] >= x2:
                indexVerticalR = i
                x2 = vertical_filtered[i][0][0]

        indexHorizontalT = 0
        indexHorizontalB = 0

        y = h / 2
        y2 = h / 2

        for i in range(0, len(horizontal_filtered)):
            if image.shape[0] > horizontal_filtered[i][0][1] >= y:
                indexHorizontalT = i
                y = horizontal_filtered[i][0][1]
            elif 0 < horizontal_filtered[i][0][1] <= y2:
                indexHorizontalB = i
                y2 = horizontal_filtered[i][0][1]

        # Get corner coordinates
        corners = [(vertical_filtered[indexVerticalL][0][0]+150, horizontal_filtered[indexHorizontalB][0][1]+150),
                   (vertical_filtered[indexVerticalL][0][0]+150, horizontal_filtered[indexHorizontalT][0][1]+150),
                   (vertical_filtered[indexVerticalR][0][0]+150, horizontal_filtered[indexHorizontalT][0][1]+150),
                   (vertical_filtered[indexVerticalR][0][0]+150, horizontal_filtered[indexHorizontalB][0][1]+150)]

        corners_pixel = [PixelCoordinate(*coordinate) for coordinate in corners]
        area = (corners_pixel[2].x - corners_pixel[0].x) * (corners_pixel[2].y - corners_pixel[0].y)

        if area < (image_or.shape[0] * image_or.shape[1]) * 0.8:
            raise ValueError("Corner detection failed")
        if plot:
            for i in range(0, len(corners)):
                cv.drawMarker(image_or, corners[i], (200, 200, 0), cv.MARKER_TILTED_CROSS, 100, 10, cv.LINE_AA)
            img2 = Image.fromarray(image_or)
            img2.show()

        return corners_pixel

    def background_removal(self, mapsheet: 'MapSheet', plot=False) -> list[PixelCoordinate]:
        """
        Remvoe the background of the map sheet. Use it alone for bonnebladen & tmk_fiel sheets.
        :param mapsheet: MapSheet object
        :param plot: Boolean to plot the image
        :return: image without background
        """

        # FIXME: Circular import
        from src import Resolution

        def find_local_maxima(xs):
            # port of
            # https://www.samproell.io/posts/signal/peak-finding-python-js/
            maxima = []
            # iterate through all points and compare direct neighbors
            for i in range(1, len(xs) - 1):
                if (xs[i] > xs[i - 1] and xs[i] > xs[i + 1]):
                    maxima.append(i)
            return maxima

        def filter_by_height(indices, xs, height):
            # port of
            # https://www.samproell.io/posts/signal/peak-finding-python-js/
            filtered = []
            for index in indices:
                if xs[index] > height:
                    filtered.append(index)
            return filtered


        # find the peak locations (indices along the axis)
        # where the value of black pixels is maximal
        image = mapsheet.get_image(resolution=Resolution.MAX)
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        bw = cv.adaptiveThreshold(image, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2)

        row, col = image.shape

        counts_ver = np.count_nonzero(bw == 0, axis=1)
        average = np.average(counts_ver)
        stddev = np.std(counts_ver)
        cumsum = np.cumsum(counts_ver)
        # count = np.sum(cumsum)
        y = cumsum  # / pixel_count
        ver_indices = find_local_maxima(counts_ver)
        ver_indices = filter_by_height(ver_indices, counts_ver, average + 4 * stddev)
        print(image.shape)
        print("Vertical", ver_indices)
        if len(ver_indices) > 2:
            if math.isclose(ver_indices[0], ver_indices[1], rel_tol=10):
                if counts_ver[ver_indices[0]] > counts_ver[ver_indices[1]]:
                    ver_indices.pop(1)
                else:
                    ver_indices.pop(0)
            if math.isclose(ver_indices[-1], ver_indices[-2], rel_tol=10):
                if counts_ver[ver_indices[-1]] > counts_ver[ver_indices[-2]]:
                    ver_indices.pop(-2)
                else:
                    ver_indices.pop(-1)
        if len(ver_indices) > 2:
            index0 = ver_indices[0]
            index1 = ver_indices[-1]
            ver_indices = [index0, index1]
        assert len(ver_indices) == 2, f"Crop lines cannot be detected"

        counts_hor = np.count_nonzero(bw == 0, axis=0)
        average = np.average(counts_hor)
        stddev = np.std(counts_hor)
        cumsum = np.cumsum(counts_hor)
        # count = np.sum(cumsum)
        y = cumsum  # / pixel_count
        hor_indices = find_local_maxima(counts_hor)
        hor_indices = filter_by_height(hor_indices, counts_hor, average + 4 * stddev)
        print("Horizontal", hor_indices)
        if len(hor_indices) > 2:
            if math.isclose(hor_indices[0], hor_indices[1], rel_tol=10):
                if counts_hor[hor_indices[0]] > counts_hor[hor_indices[1]]:
                    hor_indices.pop(1)
                else:
                    hor_indices.pop(0)
            if math.isclose(hor_indices[-1], hor_indices[-2], rel_tol=10):
                if counts_hor[hor_indices[-1]] > counts_hor[hor_indices[-2]]:
                    hor_indices.pop(-2)
                else:
                    hor_indices.pop(-1)
        if len(hor_indices) > 2:
            index0 = hor_indices[0]
            index1 = hor_indices[-1]
            hor_indices = [index0, index1]

        assert len(hor_indices) == 2, f"Crop lines cannot be detected"
        image = image[ver_indices[0]:ver_indices[-1], hor_indices[0]:hor_indices[-1]]
        corners = [(ver_indices[0], hor_indices[0]),
                   (ver_indices[0], hor_indices[1]),
                   (ver_indices[1], hor_indices[1]),
                   (ver_indices[1], hor_indices[0]),]

        corners_pixel = [PixelCoordinate(*coordinate) for coordinate in corners]
        print("Horizontal", hor_indices)
        print("Vertical", ver_indices)
        if plot:
            img = Image.fromarray(image)
            img.show()
        return corners_pixel
