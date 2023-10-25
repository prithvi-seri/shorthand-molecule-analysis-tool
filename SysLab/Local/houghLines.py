import cv2, numpy as np

# Read image
image = cv2.imread('Python/SysLab/Test Images/pentanePencil.png')	# pentane and butane no cv error

# Convert image to grayscale
gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)

# Use canny edge detection
edges = cv2.Canny(gray,50,150,apertureSize=3)
cv2.imwrite('Python/SysLab/grayscaleImage.png',edges)

# Apply HoughLinesP method to
# to directly obtain line end points
lines_list = []
lines = cv2.HoughLinesP(
			edges, # Input edge image
			1, # Distance resolution in pixels
			np.pi/180, # Angle resolution in radians
			threshold=60, # Min number of votes for valid line
			minLineLength=5, # Min allowed length of line
			maxLineGap=20 # Max allowed gap between line for joining them
			)

# Merge mirrored lines
# There will always be another line <20 pixels away that represents the other side of the drawn line

# add points into vertices array
tempVertices = []	# list of lists in format [[x coordinate, frequency, y coordinate, frequency]]
for points in lines:
	#cv2.imwrite('Python/Syslab/drawLines.png', )
	x1, y1, x2, y2 = points[0]
	tempVertices.append((x1, y1))
	tempVertices.append((x2, y2))

p = 20 # proximity threshold for merging vertices
vertices = []
while tempVertices:
	# compare with all previous points
	temp = []
	v = tempVertices.pop()
	x1, y1 = v
	temp.append(v)
	# find all nearby points
	for v2 in tempVertices:
		x2, y2 = v2
		if ((x2 - x1)**2 + (y2 - y1)**2)**0.5 < p:		# distance formula
			temp.append(v2)
	
	# remove selected vertices from tempVertices
	sumx, sumy = 0, 0
	for vertex in temp:
		if vertex in tempVertices: tempVertices.remove(vertex)
		sumx += vertex[0]
		sumy += vertex[1]
	
	vertices.append((sumx // len(temp), sumy // len(temp)))		# add new averaged point to vertex

print(vertices)

# Iterate over points
for points in lines:
	# Extracted points nested in the list
	x1, y1, x2, y2 = points[0]
	# Draw the lines joining the points
	# On the original image
	##cv2.line(image,(x1, y1), (x2, y2), (0, 255, 0), 2)
	# Maintain a lookup list for points
	lines_list.append([(x1, y1), (x2, y2)])

for vertex in vertices:
	cv2.circle(image, vertex, 5, (0, 0, 255))
	
# Save the result image
cv2.imwrite('Python/SysLab/detectedVertices.png',image)
print(f'\nCARBONS: {len(vertices)}')
print(f'HYDROGENS (estimate): {len(vertices) * 2 + 2}')
print(f'FORMULA: C{len(vertices)}H{len(vertices) * 2 + 2}')
print('*See detectedVertices.png for vertices\n')

### future improvements to consider
# potentially include ability to edit formula output which would then create new drawing of molecule
# (site works both ways, like Google Translate)