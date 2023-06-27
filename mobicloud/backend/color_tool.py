

class ColorTool(object):

	def __init__(self,red,green,blue,thickness):
		self._red = red
		self._blue = blue
		self._green = green
		self._thickness = thickness

	def rgb(self):
		rgb = [self._red,self._green,self._blue]
		return rgb

	def thickness(self):
		return self._thickness