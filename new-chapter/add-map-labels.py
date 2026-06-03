#!/usr/bin/env python3
"""Add region labels to a SimpleMaps SVG using circle coordinates."""
import sys, re

svg_path = sys.argv[1]
with open(svg_path) as f:
    content = f.read()

# Extract circle elements: class="RegionName" cx="X" cy="Y" id="XXYYY"
circles = re.findall(r'class="([^"]*)"[^>]*cx="([^"]*)"[^>]*cy="([^"]*)"[^>]*id="([^"]*)"', content)

if not circles:
    print("No circles found in SVG")
    sys.exit(0)

# Generate text labels from circle positions
# Use last 2-3 chars of ID as label (e.g., PELIM -> LIM, PECUS -> CUS)
labels = []
for name, cx, cy, id_attr in circles:
    code = id_attr[2:].upper() if len(id_attr) > 2 else id_attr.upper()
    if len(code) > 3:
        code = code[:3]
    labels.append(f'  <text x="{cx}" y="{float(cy)+4}" text-anchor="middle" fill="#888" font-size="15" font-weight="400" stroke="none" style="pointer-events:none;">{code}</text>')

# Remove existing circles
content = re.sub(r'\s*<circle[^>]*>\s*</circle>', '', content)

# Insert labels before </svg>
label_block = '\n'.join(labels)
content = content.replace('</svg>', f'{label_block}\n</svg>')

with open(svg_path, 'w') as f:
    f.write(content)

print(f"Added {len(labels)} labels")
