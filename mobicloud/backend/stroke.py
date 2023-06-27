'''
Class for Stroke object

'''

fromcolor_tool import ColorTool

class Stroke(ColorTool):

	def __init__(self,thickness,red,green,blue,pressure,points):
		super(Stroke,self).__init__(red,green,blue,thickness)
		self._pressure = pressure
		self._points = tuple(points)

	def get_point(self,i):
		return self._points[i]

	def n_points(self):
		return len(self._points)

	def thickness(self):
		color_tool = super(Stroke,self)
		return color_tool.thickness()

	def has_pressure(self):
		return self._pressure

	def __repr__(self):
		colorTool = super(Stroke,self)
		rgb = colorTool.rgb()
		s = 'pen stroke with '+str(self.n_points())+' points\n'
		s += 'rgb: ' + '(' + str(rgb[0]) + ',' + str(rgb[1]) + ',' + str(str(rgb[2])) + ')' + '\n'
		return s 

	__len__ = n_points

	__getitem__ = get_point

