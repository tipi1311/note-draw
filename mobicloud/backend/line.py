'''
Class Line
'''
from color_tool import ColorTool

class Line(ColorTool):

	def __init__(self,red,green,blue,thickness,x0,y0,x1,y1):
		super(Line,self).__init__(red,green,blue,thickness)
		self._x0 = x0
		self._y0 = y0
		self._x1 = x1
		self._y1 = y1

	
	def __repr__(self):
		colorTool = super(Line,self)
		rgb = colorTool.rgb()
		s = 'info for Line:\n'
		s += 'thickness ' + str(colorTool.thickness()) + '\n'
		s += 'rgb: ' + '(' + str(rgb[0]) + ',' + str(rgb[1]) + ',' + str(rgb[2]) + ')\n'
		s += 'x0: ' + str(self._x0) + '\n'
		s += 'y0: ' + str(self._y0) + '\n'
		s += 'x1: ' + str(self._x1) + '\n'
		s += 'y1: ' + str(self._y1) + '\n'
		return s

	def x0(self):
		return self._x0

	def y0(self):
		return self._y0

	def x1(self):
		return self._x1

	def y1(self):
		return self._y1
