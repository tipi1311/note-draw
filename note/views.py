
import base64
import os
import io
from math import pi
from cairo import SVGSurface
from django.http import HttpResponse
from django.shortcuts import render
from backend.quill_import import QuillImporter
from backend.cairo_context import CairoContext
from backend import cairodraw

class Shapes(cairodraw.CairoWidget):
    def draw(self, cr, width, height):
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # draw a rectangle
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(10, 10, width - 20, height - 20)
        cr.fill()

        # draw lines
        cr.set_source_rgb(0.0, 0.0, 0.8)
        cr.move_to(width / 3.0, height / 3.0)
        cr.rel_line_to(0, height / 6.0)
        cr.move_to(2 * width / 3.0, height / 3.0)
        cr.rel_line_to(0, height / 6.0)
        cr.stroke()

        # and a circle
        cr.set_source_rgb(1.0, 0.0, 0.0)
        radius = min(width, height)
        cr.arc(width / 2.0, height / 2.0, radius / 2.0 - 20, 0, 2 * pi)
        cr.stroke()
        cr.arc(width / 2.0, height / 2.0, radius / 3.0 - 10, pi / 3, 2 * pi / 3)
        cr.stroke()

def display_note(request,imageName,pageNumber):
	file = os.path.join('./backend/testing-notes/',imageName + '.note')
	importer = QuillImporter(file)
	qp = importer.get_page(pageNumber)
	response = HttpResponse(content_type="image/png")
	buff = io.BytesIO()
	ctr = CairoContext(buff,410,547,qp) #(buff,595,795,qp)
	ctr.draw_page()
	buff = ctr.write_to_buff(buff)
	current_page = "<img src='data:image/png;base64," + base64.b64encode(buff.getvalue()).decode() + "'/>"
	
	return render(request,'note.html',{'current_page':current_page})

def draw_shape(request):
	response = HttpResponse(content_type='image/svg+xml')
	cairodraw.draw_widget(response, Shapes)
	buff = io.BytesIO()
	cairodraw.draw_widget(buff,Shapes)
	
	return response

