import math, cv2, easyocr

# changeable
STATIC_ROOT = 'Python/SysLab/Website/static'
DETECTED_PATH = STATIC_ROOT + '/detectedVertices.png'
LINES_PATH = STATIC_ROOT + '/detectedLines.png'

def readImage(filepath):
	image = cv2.imread(filepath)
	height, width, channels = image.shape
	largeDim = height if height > width else width
	# Resize image if too large
	MAX_HEIGHT = 400
	MAX_WIDTH = 600
	largeDim = width if width > height else height
	MAX_DIM = MAX_WIDTH if width > height else MAX_HEIGHT
	if largeDim > MAX_DIM:
		image = cv2.resize(image, None, fx=MAX_DIM/largeDim, fy=MAX_DIM/largeDim, interpolation=cv2.INTER_AREA)
		cv2.imwrite(filepath, image)
	return image

def houghLines(image):
	# Convert image to grayscale
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	# Use canny edge detection
	edges = cv2.Canny(gray, 50, 150, apertureSize = 3)
	#cv2.imwrite('Python/SysLab/Local/grayscaleImage.png',edges)

	# Apply HoughLinesP method to directly obtain line end points
	lines = cv2.HoughLinesP(
				edges, # Input edge image
				1, # Distance resolution in pixels
				math.pi/180, # Angle resolution in radians
				threshold = 60, # Min number of votes for valid line ## default: 60
				minLineLength = 5, # Min allowed length of line
				maxLineGap = 20 # Max allowed gap between line for joining them
				)
	imCopy = image.copy()
	for line in lines:
		cv2.line(imCopy, (line[0][0], line[0][1]), (line[0][2], line[0][3]), (255, 0, 0))
	cv2.imwrite(LINES_PATH, imCopy)
	return lines

def initialVertices(lines):
	# add points into vertices array
	vertices = []	# list of lists in format [[x coordinate, frequency, y coordinate, frequency]]
	neighbs = {}
	for points in lines:
		x1, y1, x2, y2 = points[0]
		v1 = (x1, y1)
		v2 = (x2, y2)
		vertices.append(v1)
		# store neighbor points as well
		if v1 not in neighbs: neighbs[v1] = set()
		neighbs[v1].add(v2)
		vertices.append(v2)
		if v2 not in neighbs: neighbs[v2] = set()
		neighbs[v2].add(v1)
	return (vertices, neighbs)

def mergeVertices(tempVertices, tempNbs):
	mergeThresh = 20 # proximity threshold for merging vertices
	vertices = []
	neighbs = {}
	newPoints = {}
	while tempVertices:
		# Compare with all previous points
		temp = []
		v1 = tempVertices.pop()
		temp.append(v1)
		# Find all nearby points
		for v2 in tempVertices:
			if math.dist(v1, v2) < mergeThresh:		# distance formula
				temp.append(v2)
		
		# Create new averaged point
		sumx, sumy = 0, 0
		tempset = set()
		for vertex in temp:
			sumx += vertex[0]
			sumy += vertex[1]
			tempset |= tempNbs[vertex]

		avg = (sumx // len(temp), sumy // len(temp))
		vertices.append(avg)		# Add new averaged point to vertex
		neighbs[avg] = tempset
	
		# Remove selected vertices from tempVertices and create lookup table to map nearby points to averaged points
		for vertex in temp:
			newPoints[vertex] = avg
			if vertex != v1: tempVertices.remove(vertex)
	# Fix neighbors
	for vertex in vertices:
		nbs = neighbs[vertex]
		temp = set()
		while nbs:
			temp.add(newPoints[nbs.pop()])		# convert neighb to avg point
		for p in temp:
			nbs.add(p)							# add back to neighbs
	
	# Check if new points are still close to each other, recur if they are
	recur = False
	for i in range(len(vertices) - 1):
		for j in range(i + 1, len(vertices)):
			if math.dist(vertices[i], vertices[j]) < mergeThresh:
				recur = True
				break
	
	return mergeVertices(vertices, neighbs) if recur else (vertices, neighbs)

# Remove vertices which are between two other vertices
def removeVertices(vertices, neighbs):
	removeThresh = 10	# cutoff value for distance from line
	removedNbs = set()
	for vertex in vertices:
		nbs = neighbs[vertex]
		if vertex in removedNbs: continue
		x1, y1 = vertex
		removeNbs = set()
		for neighb in nbs:
			if neighb in removeNbs: continue
			x2, y2 = neighb
			m = (y2 - y1) / (x2 - x1)
			c = y2 - x2 * m
			mperp = -1 / m
			for n2 in nbs:
				x3, y3 = n2
				if x2 == x3 and y2 == y3: continue
				# find closest point on line
				cperp = y3 - x3 * mperp
				xint = (cperp - c) / (m - mperp)
				yint = m * xint + c
				# check distance
				if math.dist((xint, yint), n2) < removeThresh and math.dist((x1, y1), (x2, y2)) > math.dist((x1, y1), (x3, y3)):
					removeNbs.add(n2)
		nbs -= removeNbs
		removedNbs |= removeNbs
	for vertex in removedNbs:
		vertices.remove(vertex)
		del neighbs[vertex]
	for vertex in vertices:
		for nb in removedNbs:
			if nb in neighbs[vertex]: neighbs[vertex].remove(nb)
	return (vertices, neighbs)

def drawVertices(image, vertices):
	for vertex in vertices:
		cv2.circle(image, vertex, 5, (0, 0, 255))
	cv2.imwrite(DETECTED_PATH, image)	# save image

# Count number of carbons and hydrogens (without additional elements for now)
def countElements(vertices, neighbs):
	carbons = len(vertices)
	hydrogens = 0
	for vertex in vertices:
		hydrogens += 4 - len(neighbs[vertex])
	return (carbons, hydrogens)

def printStats(vertices, neighbs, carbons, hydrogens):
	print(f'\nCARBONS: {carbons}')
	print(f'HYDROGENS (estimate): {hydrogens}')
	print(f'FORMULA: C{carbons}H{hydrogens}')
	print('*See detectedVertices.png for vertices\n')
	print('Vertices: Neighbors')
	for vertex in sorted(vertices):
		print(f'{vertex}: {neighbs[vertex]}')

def readLetters(filepath, image):		# try limiting size of identified letters to increase accuracy
	reader = easyocr.Reader(['en'], gpu=False)
	results = reader.readtext(filepath, allowlist='ABCDEFGHIKLMNOPRSTUVWXYZabcdefghiklmnoprstuvwxyz')	# no j or q because they are not found on the periodic table
	print(results)
	for letter in results:
		for coord in letter[0]:
			cv2.circle(image, coord, 5, (255, 0, 0))	
	cv2.imwrite(DETECTED_PATH, image)

def analyse(filepath):
	image = readImage(filepath)

	lines = houghLines(image)
	tempVertices, tempNbs = initialVertices(lines)
	vertices, neighbs = mergeVertices(tempVertices, tempNbs)
	vertices, neighbs = removeVertices(vertices, neighbs)
	
	drawVertices(image, vertices)
	#readLetters(filepath, image)
	carbons, hydrogens = countElements(vertices, neighbs)
	printStats(vertices, neighbs, carbons, hydrogens)

	return [f'Formula: C{len(vertices)}H{len(vertices) * 2 + 2}', f'{len(vertices)} Endpoints Identified']