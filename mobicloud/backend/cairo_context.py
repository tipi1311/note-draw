import cairo
import gi
import math
import os

gi.require_version('Gtk','3.0')
from gi.repository import GdkPixbuf
from gi.repository import Gdk as gdk
from quill_import import QuillImporter

class CairoContext(object):

	def __init__(self,dest,width,height,quillpage):
		self._width = width 
		self._height = height
		self._quillpage = quillpage
		if quillpage.aspect_ratio > 1:
			self._height,self._width = self._width, self._height
		self._surface = cairo.ImageSurface(cairo.FORMAT_RGB24,self._width,self._height)
		#self._surface = cairo.SVGSurface(dest,width,height)
		self._context = cairo.Context(self._surface)
		self._pen_scale_factor = float(5.0/0.003)
	
	def init_page(self):
		self._context.set_line_cap(cairo.LINE_CAP_ROUND)
		self._context.set_line_join(cairo.LINE_JOIN_ROUND)
		h = self._height
		w = h * self._quillpage.aspect_ratio
		if w > self._width:
			w = self._width
			h = w / self._quillpage.aspect_ratio
		self._context.identity_matrix() 
		
		self._context.scale(h,h)
		#dx = (self._width - w) / h
		#dy = (self._height - h) / h
		#self._context.translate(dx/2,dy/2)
		self._context.set_source_rgb(1,1,1) 
		#self._context.rectangle(1,1,self._width-1,self._height-1) 
		self._context.rectangle(0,0,self._width,self._height)
		#self._context.set_line_width(1)
		#self._context.stroke()
		self._context.fill()

	def write_image(self,response):
		self._surface.write_to_png(response)
		return response

	def write_to_buff(self,dest):
		self._surface.write_to_png(dest)
		return dest

	def draw_image(self):
		list_images = self._quillpage.images
		if (len(list_images) > 0):
			ctr = self._context
			for image in list_images:
				data = image.data()
				loader = GdkPixbuf.PixbufLoader.new_with_type('jpeg')
				loader.write(data)
				pixbuf = loader.get_pixbuf()
				loader.close()
				# Create image surface
				image_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,pixbuf.get_width(),pixbuf.get_height())
				image_context = cairo.Context(image_surface)
				gdk.cairo_set_source_pixbuf(image_context,pixbuf,0,0)
				image_context.paint()
				image_context.stroke()
				ctr.save()

				ctr.translate(image.x0(),image.y0())
				w = (image.x1() - image.x0()) / image_surface.get_width()
				h = (image.y1() - image.y0()) / image_surface.get_height()
				ctr.scale(w,h)
				ctr.set_source_surface(image_surface,0,0)
				ctr.paint()
				ctr.stroke()
				ctr.restore()

	def draw_stroke(self):
		list_strokes = self._quillpage.strokes
		if (len(list_strokes) > 0):
			ctr = self._context
			for stroke in list_strokes:
				rgb = stroke.rgb()
				ctr.set_source_rgb(rgb[0]/255,rgb[1]/255,rgb[2]/255)
				if stroke.has_pressure():
					p1 = stroke.get_point(0)
					for i in range(stroke.n_points() - 1):
						p0 = p1
						p1 = stroke.get_point(i+1)
						ctr.set_line_width(stroke.thickness() / self._pen_scale_factor * (p0[2] + p1[2])/2)
						ctr.move_to(p0[0],p0[1])
						ctr.line_to(p1[0],p1[1])
						ctr.stroke()
				else:
					ctr.set_line_width(stroke.thickness() / self._pen_scale_factor)
					p1 = stroke.get_point(0)
					for i in range(stroke.n_points() - 1):
						p0 = p1
						p1 = stroke.get_point(i+1)
						ctr.move_to(p0[0],p0[1])
						ctr.line_to(p1[0],p1[1])
						ctr.stroke()

	def draw_table(self):
		list_tables = self._quillpage.tables
		if (len(list_tables) > 0):
			ctr = self._context
			for table in list_tables:
				print(table)
				ctr.set_line_width(table.thickness() / self._pen_scale_factor)
				rgb = table.rgb()
				ctr.set_source_rgb(rgb[0],rgb[1],rgb[2])
				rowTopCoord = table.computeRowLine()
				colRightCoord = table.computeColLine()
				#Draw border
				ctr.move_to(table.left(),table.top())
				ctr.line_to(table.left(),table.bottom())
				ctr.line_to(table.right(),table.bottom())
				ctr.line_to(table.right(),table.top())
				ctr.line_to(table.left(),table.top())
				#Draw inner row
				for innerRow in rowTopCoord:
					ctr.move_to(table.left(),table.top() + innerRow)
					ctr.line_to(table.right(),table.top() + innerRow)
				for innerCol in colRightCoord:
					ctr.move_to(table.left() + innerCol, table.top())
					ctr.line_to(table.left() + innerCol, table.bottom())
				ctr.stroke()

	def draw_oval(self):
		list_ovals = self._quillpage.ovals
		if (len(list_ovals) > 0):
			ctr = self._context
			for oval in list_ovals:
				ctr.set_line_width(oval.thickness() / self._pen_scale_factor)
				rgb = oval.rgb()
				ctr.set_source_rgb(rgb[0],rgb[1],rgb[2])
				center_x,center_y = oval.center_coordinate()
				factor = (center_y - oval.top()) / (center_x - oval.left()) 
				ctr.scale(1,factor)
				ctr.arc(center_x,center_y/factor,center_x - oval.left(),0,2*math.pi)
				ctr.stroke()
				#rescale
				ctr.scale(1,1/factor)

	def draw_rectangle(self):
		list_rectangles = self._quillpage.rectangles
		if (len(list_rectangles) > 0):
			ctr = self._context
			for rectangle in list_rectangles:
				ctr.set_line_width(rectangle.thickness() / self._pen_scale_factor)
				rgb = rectangle.rgb()
				ctr.set_source_rgb(rgb[0],rgb[1],rgb[2])
				ctr.rectangle(rectangle.left(),rectangle.top(),rectangle.width(),rectangle.height())
				ctr.stroke()

	def draw_triangle(self):
		list_triangles = self._quillpage.triangles
		if len(list_triangles) > 0:
			ctr = self._context
			for triangle in list_triangles:
				ctr.set_line_width(triangle.thickness() / self._pen_scale_factor)
				rgb = triangle.rgb()
				ctr.set_source_rgb(rgb[0],rgb[1],rgb[2])
				ctr.move_to(triangle.middle(),triangle.top())
				ctr.line_to(triangle.left(),triangle.bottom())
				ctr.line_to(triangle.right(),triangle.bottom())
				ctr.line_to(triangle.middle(),triangle.top())
				ctr.stroke()

	def draw_line(self):
		list_lines = self._quillpage.lines
		if len(list_lines) > 0:
			ctr = self._context
			for line in list_lines:
				ctr.set_line_width(line.thickness() / self._pen_scale_factor)
				rgb = line.rgb()
				ctr.set_source_rgb(rgb[0],rgb[1],rgb[2])
				ctr.move_to(line.x0(), line.y0())
				ctr.line_to(line.x1(), line.y1())
				ctr.stroke()

	def draw_textBox(self):
		list_textboxes = self._quillpage.textboxes
		if len(list_textboxes) > 0:
			ctr = self._context
			for textbox in list_textboxes:
				#set surface for the text
				textbox_width = textbox.right() - textbox.left()
				textbox_height = textbox.bottom() - textbox.top()
				spacing_width = (textbox_width/25)
				spacing_height = (textbox_height/2.5)
				font_size = textbox.textSize() * textbox.fontScale() / (842*842*.52/self._height)
				# Take this out after no more bug, leave rectagle now to indicate area of textbox
				ctr.rectangle(textbox.left(),textbox.top(),textbox_width,textbox_height)
				ctr.set_source_rgb(0,0,0)
				ctr.stroke()

				rgb = textbox.rgb()
				ctr.set_source_rgb(rgb[0],rgb[1],rgb[2])
				ctr.set_font_size(font_size)

				if textbox.isItalic():
					format_italic = cairo.FONT_SLANT_ITALIC
				else:
					format_italic = cairo.FONT_SLANT_NORMAL

				if textbox.isBold():
					format_bold = cairo.FONT_WEIGHT_BOLD
				else:
					format_bold = cairo.FONT_WEIGHT_NORMAL

				ctr.select_font_face("Arial",format_italic,format_bold)
				constant_left = textbox.left() + spacing_width
				
				nextline = 1
				validWord = ''
				attemptWord = ''
				considered_words=[]
				list_words = textbox.breakWords()
				while(True):  
					if len(list_words) == 0 and len(considered_words) == 0:
						ctr.move_to(textbox.left() + spacing_width,textbox.top() + nextline * spacing_height)
						ctr.show_text(validWord)
						break
					if len(considered_words) == 0:
						considered_words.append(list_words.pop(0))
					
					currentWord = considered_words.pop(0)
					if validWord != '':
						attemptWord = validWord + ' ' + currentWord
					else:
						attemptWord = currentWord
					
					x_bearing, y_bearing, text_width, text_height, dx, dy = ctr.text_extents(attemptWord)
					if (textbox_width - text_width >= spacing_width):
						validWord = attemptWord
					if (textbox_width - text_width < spacing_width):
						ctr.move_to(textbox.left() + spacing_width,textbox.top() + nextline * spacing_height)
						if validWord != '':	
							considered_words.insert(0,currentWord)
						else :
							lastIndex = len(attemptWord)
							while(True):
								text_subStr = attemptWord[:lastIndex]
								x_bearing, y_bearing, text_width, text_height, dx, dy = ctr.text_extents(text_subStr)
								if (textbox_width - text_width >= spacing_width):
									validWord = text_subStr
									considered_words.insert(0,attemptWord[lastIndex:])
									break
								lastIndex -= 1
						ctr.show_text(validWord)
						nextline += 1
						validWord = ''
		

	def draw_page(self):
		self.init_page()
		self.draw_oval()
		self.draw_image()
		self.draw_triangle()
		self.draw_line()
		self.draw_textBox()
		self.draw_rectangle()
		self.draw_table()
		self.draw_stroke()
		#self._surface.finish()
		
		


