'''
class TextBox
'''
class TextBox(object):

	def __init__(self,red,green,blue,left,right,top,bottom,textStr,textSize,isBold,isItalic,isUnderline):
		self._red = red
		self._green = green
		self._blue = blue
		self._left = left
		self._right = right
		self._top = top
		self._bottom = bottom
		self._textStr = textStr
		self._textSize = textSize
		self._isBold = isBold
		self._isItalic = isItalic
		self._isUnderline = isUnderline
		self._font_size_scale_factor = 2.5

	def __repr__(self):
		s = 'info for TextBox:\n'
		s += 'rgb: ' + '(' + str(self._red) + ',' + str(self._green) + ',' + str(self._blue) + ')\n'
		s += 'formatText: ' + '{' + 'isBold:' + str(self._isBold) + ',' + 'isItalic:' + str(self._isItalic) + ',' + 'isUnderline:' + str(self._isUnderline) + '}\n'
		s += 'textString: ' + self._textStr + '\n'
		s += 'textSize: ' + str(self._textSize) + '\n'
		s += 'left: ' + str(self._left) + '\n'
		s += 'right: ' + str(self._right) + '\n'
		s += 'top: ' + str(self._top) + '\n'
		s += 'bottom: ' + str(self._bottom) + '\n'
		return s

	def breakWords(self):
		text = self._textStr
		list_words = []
		word = ''
		for index in range(len(text)):
			if text[index] != ' ':
				word += text[index]
			if word != ' ' and text[index] == ' ':
				list_words.append(word)
				word = ''
			if index == len(text) - 1:
				list_words.append(word)
		return list_words

	def fontScale(self):
		return self._font_size_scale_factor

	def left(self):
		return self._left

	def right(self):
		return self._right

	def top(self):
		return self._top

	def bottom(self):
		return self._bottom

	def textStr(self):
		return self._textStr

	def textSize(self):
		return self._textSize

	def isBold(self):
		return self._isBold

	def isItalic(self):
		return self._isItalic

	def isUnderline(self):
		return self._isUnderline

	def rgb(self):
		rgb = [self._red,self._green,self._blue]
		return rgb