from ..custom_types import Cv2Image, PixelCoordinate
from .baseclass import Mask

from PIL import Image
import cv2 as cv
import numpy as np
import math


class MaskGenerator:
    maximum_corner_count: int
    resolution: 'Resolution'
    def from_mapsheet(self, sheet_image: Cv2Image) -> Mask:
        ...

    def corner_detection(self, map_sheet: 'MapSheet') -> list[PixelCoordinate]:
        from src.mapsheet import MapSheet, Resolution
        image = map_sheet.get_image(resolution=Resolution.MAX)

        image = image[150:image.shape[0] - 150, 150:image.shape[1] - 150]
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
                print("Horizontal angle:", angle, "\n")
        for j in range(0, len(linesP_vertical)):
            angle = math.atan2(linesP_vertical[j][0][3] - linesP_vertical[j][0][1],
                               linesP_vertical[j][0][2] - linesP_vertical[j][0][0]) * 180 / math.pi
            if math.isclose(angle, 90, abs_tol=4) or math.isclose(angle, -90, abs_tol=4):
                vertical_filtered.append(linesP_vertical[j])
                print("Vertical angle:", angle)

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

            if vertical_filtered[i][0][0] <= x:
                indexVerticalL = i
                x = vertical_filtered[i][0][0]
            elif vertical_filtered[i][0][0] >= x2:
                indexVerticalR = i
                x2 = vertical_filtered[i][0][0]

        indexHorizontalT = 0
        indexHorizontalB = 0

        y = h / 2
        y2 = h / 2

        for i in range(0, len(horizontal_filtered)):

            if horizontal_filtered[i][0][1] >= y:
                indexHorizontalT = i
                y = horizontal_filtered[i][0][1]
            elif horizontal_filtered[i][0][1] <= y2:
                indexHorizontalB = i
                y2 = horizontal_filtered[i][0][1]

        # Get corner coordinates
        corners = [(vertical_filtered[indexVerticalL][0][0], horizontal_filtered[indexHorizontalB][0][1]),
                   (vertical_filtered[indexVerticalL][0][0], horizontal_filtered[indexHorizontalT][0][1]),
                   (vertical_filtered[indexVerticalR][0][0], horizontal_filtered[indexHorizontalT][0][1]),
                   (vertical_filtered[indexVerticalR][0][0], horizontal_filtered[indexHorizontalB][0][1])]

        image = cv.cvtColor(image, cv.COLOR_GRAY2BGR)
        for i in range(0, len(corners)):
            cv.drawMarker(image, corners[i], (200, 200, 0), cv.MARKER_TILTED_CROSS, 100, 10, cv.LINE_AA)
        corners_pixel = [PixelCoordinate(*coordinate) for coordinate in corners]
        img2 = Image.fromarray(image)
        img2.show()

        return corners_pixel
