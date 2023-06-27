from cairo import Context, SVGSurface

# Create a GTK+ widget on which we will draw using Cairo
class CairoWidget:

    def __init__(self, Surface = None):
        if Surface == None:
            Surface = SVGSurface
        
        self.Surface = Surface
    
    def draw(self, cr, width, height):
        # Fill the background with gray
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.rectangle(0, 0, width, height)
        cr.fill()


def draw_widget(dest, Widget, Surface = SVGSurface, width = 200, height = 200):
    """
    Convenience function to output CairoWidget to a buffer
    """
    widget = Widget(Surface)
    surface = widget.Surface(dest, width, height)
    widget.draw(Context(surface), width, height)
    surface.finish()

