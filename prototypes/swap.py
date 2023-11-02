import json
import re


def swap_width_height(svg_value):
    """Swap width and height values in an SVG string and also swap x and y values in the polygon points."""
    match = re.search(r'width="(\d+)" height="(\d+)"', svg_value)
    if match:
        width, height = match.groups()
        svg_value = svg_value.replace(f'width="{width}" height="{height}"', f'width="{height}" height="{width}"')

    # Capture and swap x,y values in the polygon points
    points_match = re.search(r'<polygon points="([\d, ]+)"', svg_value)
    if points_match:
        points = points_match.group(1)
        swapped_points = ' '.join([','.join(reversed(pt.split(','))) for pt in points.split(' ')])
        svg_value = svg_value.replace(points, swapped_points)

    return svg_value


# Load the JSON from the file
with open('/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/project/phase1/results_wp3/bonnebladen/FULL_bonne_combined.json', 'r') as file:
    data = json.load(file)

# Loop over each item and update the 'value' of 'SvgSelector'
for item in data['items']:
    if 'selector' in item['target'] and item['target']['selector']['type'] == 'SvgSelector':
        svg_value = item['target']['selector']['value']
        item['target']['selector']['value'] = swap_width_height(svg_value)

# Write the modified JSON back to the file
with open('/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/project/phase1/results_wp3/bonnebladen/FULL_bonne_combined3.json', 'w') as file:
    json.dump(data, file, indent=4)
