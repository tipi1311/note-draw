'''
Class for Triangle object
'''

from mobicloud.backend.color_tool import ColorTool

class Triangle(ColorTool):

	def __init__(self,thickness,red,green,blue,x0,y0,x1,y1):
		super(Triangle,self).__init__(red,green,blue,thickness)
		self._left = x0
		self._right = y0
		self._top = x1
		self._bottom = y1
		

	def __repr__(self):
		colorTool = super(Triangle,self)
		rgb = colorTool.rgb()
		s = 'info for triangle\n'
		s += 'thickness ' + str(colorTool.thickness()) + '\n'
		s += 'rgb: ' + '(' + str(rgb[0]) + ',' + str(rgb[1]) + ',' + str(str(rgb[2])) + ')' + '\n'
		s += 'left: ' + str(self._left) + '\n'
		s += 'right: ' + str(self._right) + '\n'
		s += 'top: ' + str(self._top) + '\n'
		s += 'bottom: ' + str(self._bottom) + '\n'
		return s

	def left(self):
		return self._left

	def right(self):
		return self._right

	def top(self):
		return self._top

	def bottom(self):
		return self._bottom

	def middle(self):
		return (self._left + self._right) / 2


