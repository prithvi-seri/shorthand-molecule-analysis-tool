import math, cv2, easyocr, numpy as np
from PIL import Image, ImageFilter
import os	# for testing

# changeable
ROOT = 'C:/Users/prith/OneDrive/Desktop/Code/Python/SysLab'
INPUT_PATH = ROOT + '/Test Images/Generated/2,3-dimethylbutane.png'
DETECTED_PATH = ROOT + '/Local/detectedVertices.png'
LINES_PATH = ROOT + '/Local/detectedLines.png'

def calcLine(p1, p2):
	x1, y1 = p1
	x2, y2 = p2
	m = (y2 - y1) / (x2 - x1)
	b = y2 - x2 * m
	return (m, b)	# (slope, intercept)

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
	# gray = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)[1]
	# gray = cv2.GaussianBlur(gray, (5, 5), 0)
	cv2.imwrite(ROOT + '/Local/bwImage.png', gray)

	# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
	# opening = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=3)
	# cv2.imwrite(ROOT + '/Local/morphImage.png', opening)

	# cv2.imshow('im', opening)
	# cv2.waitKey(0)
	# cv2.destroyAllWindows()

	# Use canny edge detection
	edges = cv2.Canny(gray, 50, 150, apertureSize = 3)
	cv2.imwrite(ROOT + '/Local/edgeImage.png', edges)

	# # Smooth edges
	# pImage = Image.open(ROOT + '/Local/grayscaleImage.png')
	# pImage = pImage.filter(ImageFilter.ModeFilter(size=1))
	# pImage.save(ROOT + '/Local/smoothImage.png')

	# Apply HoughLinesP method to directly obtain line endpoints
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
		cv2.line(imCopy, (line[0][0], line[0][1]), (line[0][2], line[0][3]), (255, 0, 0), 2)
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
			if math.dist(v1, v2) < mergeThresh:
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

def fixNeighbs(vertices, neighbs, image):
	temp = []
	for vertex in vertices:
		x, y = vertex
		for v2 in vertices:
			if vertex == v2 or v2 in neighbs[vertex]: continue
			m, b = calcLine(vertex, v2)
			count = 0
			for i in range(1, 11):
				count += sum(val < 60 for val in image[int(y + m * i), x + i]) == 3		# all values in rgb list are <50
			if count > 9: temp.append((vertex, v2))
	print()

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
			b = y2 - x2 * m
			mperp = -1 / m
			for n2 in nbs:
				x3, y3 = n2
				if x2 == x3 and y2 == y3: continue
				# find closest point on line
				bperp = y3 - x3 * mperp
				xint = (bperp - b) / (m - mperp)
				yint = m * xint + b
				# check distance
				if math.dist((xint, yint), n2) < removeThresh and math.dist((x1, y1), (x2, y2)) > math.dist((x1, y1), (x3, y3)) and math.dist((x1, y1), (x2, y2)) < math.dist((x2, y2), (x3, y3)): # last case ensures point isn't between two other points
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
	vertices, neighbs = initialVertices(lines)
	vertices, neighbs = mergeVertices(vertices, neighbs)
	#fixNeighbs(vertices, neighbs, image)
	drawVertices(image.copy(), vertices)	# show temporary vertices
	vertices, neighbs = removeVertices(vertices, neighbs)
	drawVertices(image, vertices)
	#readLetters(filepath, image)
	carbons, hydrogens = countElements(vertices, neighbs)
	printStats(vertices, neighbs, carbons, hydrogens)

	return [f'Formula: C{len(vertices)}H{len(vertices) * 2 + 2}', f'{len(vertices)} Vertices Identified']

analyse(INPUT_PATH)