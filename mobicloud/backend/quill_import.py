import tarfile
import struct
import os
import cairo

from backend.base import ImporterBase, QuillImporterError
from backend.triangle import Triangle
from backend.line import Line
from backend.textbox import TextBox
from backend.rectangle import Rectangle
from backend.oval import Oval
from backend.table import Table
from backend.stroke import Stroke
from backend.image import Image

current_path = os.path.dirname(os.path.realpath(__file__))

class QuillImporter(ImporterBase):

    def __init__(self,quill_filename):
        self._filename = quill_filename
        with tarfile.open(self._filename, "r") as t:
            self._open_quill_archive(t)

    def _open_quill_archive(self,t):
        self._index = None
        index_files = []

        #List of tarfile
        for f in t.getmembers():
            if f.name.endswith('index') and not f.name.endswith('auto_index'):
                index_files += [f,]

        if len(index_files) == 1: #case there is index file
            self._index = QuillIndex(t.extractfile(index_files[0]))
            q = self._index
            notebook_dir = os.path.split(index_files[0].name)[0]
            self._page_filenames = [notebook_dir+'/page_'+page_uuid.decode('utf-8')+'.page' for page_uuid in q.page_uuids]
        else:
            self._page_filenames = []
            for f in t.getmembers():
                if f.name.endswith('.quill_data'):
                    self._page_filenames += [f.name,]

    def uuid(self):
        if self._index:
            return self._index.uuid
        return None

    def title(self):
        if self._index:
            return self._index.title
        return None

    def mtime_millis(self):
        if self._index:
            return self._index.mtime[0]
        return None

    def ctime_millis(self):
        if self._index:
            return self._index.ctime[0]
        return None

    def n_pages(self):
        if self._index:
            return self._index.npages[0]
        return len(self._page_filenames)

    def get_page(self,n):
        page_filename = self._page_filenames[n]
        with tarfile.open(self._filename, 'r') as t:
            page_file = t.extractfile(page_filename)
            qp = QuillPage(page_file, QuillBlob(t))

        return qp

class QuillBlob(object):
    """
    Loader for contained binary objects (e.g. images)
    """
    def __init__(self,tar):
        self._tar = tar

    def get(self, uuid):
        """
        Return the object with given uuid
        """
        fileinfo = self._find_uuid(uuid)
        f = self._tar.extractfile(fileinfo)
        try:
            data = f.read()
            return data
        except IOError:
            raise QuillImporterError('failed to read binary object')
        finally:
            f.close()

    def _find_uuid(self, uuid):
        temp = uuid.decode('utf-8')
        for f in self._tar.getmembers():
            name = os.path.split(f.name)[-1]
            if name.startswith(temp):
                return f
        raise QuillImporterError('binary object missing from Quill file')


class QuillIndex(object):

    def __init__(self, index_file):
        fp = index_file
        self.version = struct.unpack(">i", fp.read(4))
        #Check all the current page version
        if not (self.version == (4,) or self.version == (7,)):
            raise QuillImporterError('wrong page version')
        self.npages = struct.unpack(">i",fp.read(4))
        self.page_uuids = []

        for x in range(self.npages[0]):
            nbytes = struct.unpack(">h", fp.read(2))
            u = fp.read(36)
            self.page_uuids.append(u)

        self.currentPage = struct.unpack(">i",fp.read(4))
        nbytes = struct.unpack(">h", fp.read(2))
        self.title = fp.read(nbytes[0]).decode('utf-8')
        self.ctime = struct.unpack(">q", fp.read(8))
        self.mtime = struct.unpack(">q", fp.read(8))
        nbytes = struct.unpack(">h", fp.read(2))
        self.uuid = fp.read(36)

    def __repr__(self):
        s = 'File version: '+str(self.version)+'\n'
        s += 'Title: ' + self.title + '\n'
        s += 'ctime: ' + str(self.ctime) + '\n'
        s += 'mtime: ' + str(self.mtime) + '\n'
        for i,p in enumerate(self.page_uuids):
            s += 'page ' + str(i) + ': ' + str(p) + '\n'
        return s

class QuillPage(object):
    # Purely arbitrary
    # A line-width of 0.003 gives a good visual approximation to Quill's pen thickness of 5
    pen_scale_factor = float(5.0/0.003)

    
    def loadTagSet(self,fp):
        self.tsversion = struct.unpack(">i", fp.read(4))
        if self.tsversion != (1,):
            raise QuillImporterError('wrong tag set version')
        self.ntags = struct.unpack(">i", fp.read(4))
        self.tags = [self.read_tag() for i in range (self.ntags[0])]
        foo = struct.unpack(">i", fp.read(4))
        foo = struct.unpack(">i", fp.read(4))


    def loadPage_v13(self,fp):
        self.nimages = struct.unpack(">i", fp.read(4))
        self.images = [ self.read_image() for i in range(self.nimages[0]) ]

        self.nlines = struct.unpack(">i", fp.read(4))
        self.lines = [ self.read_line() for i in range(self.nlines[0]) ]

        self.nRectangle = struct.unpack(">i", fp.read(4))
        self.rectangles = [ self.read_rectangle() for i in range(self.nRectangle[0])]

        self.nOval = struct.unpack(">i", fp.read(4))
        self.ovals = [ self.read_oval() for i in range(self.nOval[0])]

        self.nTriangle = struct.unpack(">i", fp.read(4))
        self.triangles =  [ self.read_triangle() for i in range(self.nTriangle[0])]

        self.nTable = struct.unpack(">i", fp.read(4))
        self.tables = [self.read_table() for i in range(self.nTable[0])]

        self.nstrokes = struct.unpack(">i", fp.read(4))
        self.strokes = [ self.read_stroke() for i in range(self.nstrokes[0]) ]

    def read_tag(self):
        fp = self.fp
        self.tsversion = struct.unpack(">i", fp.read(4))
        if self.tversion != (1,):
            raise QuillImporterError('wrong tag version')
        nbytes = struct.unpack(">h", fp.read(2))
        tag = {}
        tag["tag"] = fp.read(nbytes[0]).decode("utf-8")
        tag["autogenerated"] = struct.unpack(">?", fp.read(1))[0]
        tag["ctime"] = struct.unpack(">q", fp.read(8))[0]
        foo = struct.unpack(">q", fp.read(8))

    def read_textbox(self):
        fp = self.fp
        self.textbox_version = struct.unpack(">i", fp.read(4))
        if self.textbox_version != (1,):
            raise QuillImporterError('wrong textbox version')

        self.textbox_tool = struct.unpack(">i", fp.read(4))
        if self.textbox_tool != (4,):
            raise QuillImporterError('wrong tool textbox version')

        left = struct.unpack(">f", fp.read(4))
        right = struct.unpack(">f", fp.read(4))
        top = struct.unpack(">f", fp.read(4))
        bottom = struct.unpack(">f", fp.read(4))

        nbytes = struct.unpack(">h", fp.read(2))
        textStr = fp.read(nbytes[0]).decode("utf-8")

        textFontSize = struct.unpack(">i", fp.read(4))
        textColor = struct.unpack(">I", fp.read(4))

        red = (textColor[0] >> 16) & 0xFF
        green = (textColor[0] >> 8) & 0xFF
        blue = textColor[0] & 0xFF

        isBold = struct.unpack(">?", fp.read(1))
        isItalic = struct.unpack(">?", fp.read(1))
        isUnderline = struct.unpack(">?", fp.read(1))

        return TextBox(red,green,blue,left[0],right[0],top[0],bottom[0],textStr,textFontSize[0],isBold[0],isItalic[0],isUnderline[0])

    def read_image(self):
        fp = self.fp
        self.image_version = struct.unpack(">i", fp.read(4))
        if self.image_version != (1,):
            raise QuillImporterError('wrong version of image')

        uuid_nbytes = struct.unpack(">h", fp.read(2))
        uuid = fp.read(36)

        top_left = struct.unpack(">f", fp.read(4))
        top_right = struct.unpack(">f", fp.read(4))
        bottom_left = struct.unpack(">f", fp.read(4))
        bottom_right = struct.unpack(">f", fp.read(4))
        constrain_aspect = struct.unpack(">?", fp.read(1))

        return Image(uuid,top_left[0],top_right[0],bottom_left[0],bottom_right[0],constrain_aspect[0],self._blob_loader.get(uuid))

    
    def getToolInfo(self,fp):
        pen_color = struct.unpack(">I", fp.read(4))
        red = (pen_color[0] >> 16) & 0xFF
        green = (pen_color[0] >> 8) & 0xFF
        blue = pen_color[0] & 0xFF
        thickness = struct.unpack(">i", fp.read(4))
        toolint = struct.unpack(">i", fp.read(4))
        return (red,green,blue,thickness,toolint)

    def read_line(self):
        fp = self.fp
        self.line_version = struct.unpack(">i", fp.read(4))
        if version != (1,):
            raise QuillImporterError('wrong version of line')

        red,green,blue,thickness,toolint = self.getToolInfo(fp)
        if toolint != (5,):
            raise QuillImporterError('wrong line tool')

        xy = struct.unpack(">ffff", fp.read(4*4))
        return Line(red,green,blue,thickness[0],xy[0],xy[1],xy[2],xy[3])

    def read_rectangle(self):
        fp = self.fp
        self.rectangle_version = struct.unpack(">i", fp.read(4))
        if self.rectangle_version != (1,):
            raise QuillImporterError('wrong version of rectangle')

        red,green,blue,thickness,toolint = self.getToolInfo(fp)
        if toolint != (10,):
            raise QuillImporterError('wrong rectangle tool')

        top_left = struct.unpack(">f", fp.read(4))
        top_right = struct.unpack(">f", fp.read(4))
        bottom_left = struct.unpack(">f", fp.read(4))
        bottom_right = struct.unpack(">f", fp.read(4))
        return Rectangle(thickness[0],red,green,blue,top_left[0],top_right[0],bottom_left[0],bottom_right[0])

    def read_oval(self):
        fp = self.fp
        self.oval_version = struct.unpack(">i", fp.read(4))
        if self.oval_version != (1,):
            raise QuillImporterError('wrong version of oval')

        red,green,blue,thickness,toolint = self.getToolInfo(fp)
        if toolint != (11,):
            raise QuillImporterError('wrong oval tool')

        top_right = struct.unpack(">f", fp.read(4))
        top_left = struct.unpack(">f", fp.read(4))
        bottom_left =struct.unpack(">f", fp.read(4))
        bottom_right = struct.unpack(">f", fp.read(4))

        return Oval(thickness[0],red,green,blue,top_left[0],top_right[0],bottom_left[0],bottom_right[0])

    def read_triangle(self):
        fp = self.fp
        self.triangle_version = struct.unpack(">i", fp.read(4))
        if self.triangle_version != (1,):
            raise QuillImporterError('wrong version of triangle')

        red,green,blue,thickness,toolint = self.getToolInfo(fp)
        if toolint != (12,):
            raise QuillImporterError('wrong triangle tool')

        top_left = struct.unpack(">f", fp.read(4))
        top_right = struct.unpack(">f", fp.read(4))
        bottom_left = struct.unpack(">f", fp.read(4))
        bottom_right = struct.unpack(">f", fp.read(4))
        return Triangle(thickness[0],red,green,blue,top_left[0],top_right[0],bottom_left[0],bottom_right[0])

    def read_table(self):
        fp = self.fp
        self.table_version = struct.unpack(">i", fp.read(4))
        if self.table_version != (1,):
            raise QuillImporterError('wrong version of table')

        red,green,blue,thickness,toolint = self.getToolInfo(fp)
        if toolint != (15,):
            raise QuillImporterError('wrong table tool')

        top_left = struct.unpack(">f", fp.read(4))
        top_right = struct.unpack(">f", fp.read(4))
        bottom_left = struct.unpack(">f", fp.read(4))
        bottom_right = struct.unpack(">f", fp.read(4))
        rowNum = struct.unpack(">i", fp.read(4))
        colNum = struct.unpack(">i", fp.read(4))
        rowPercentHeight = []
        colPercentWidth = []

        for i in range(rowNum[0]):
            rowPercentHeight += [struct.unpack(">f", fp.read(4))[0],]

        for i in range(colNum[0]):
            colPercentWidth += [struct.unpack(">f", fp.read(4))[0],]

        return Table(thickness[0],red,green,blue,top_left[0],top_right[0],bottom_left[0],bottom_right[0],rowPercentHeight,colPercentWidth)

    def read_stroke(self):
        fp = self.fp
        self.stroke_version = struct.unpack(">i", fp.read(4))
        v = self.stroke_version[0]
        if v < 1 or v > 3:
            raise QuillImporterError('wrong version of stroke')

        red,green,blue,thickness,toolint = self.getToolInfo(fp)
        fountain_pen = (toolint == (0,) or toolint== (8,))
        if toolint[0] < 0 or toolint[0]>=17:
            raise QuillImporterError('wrong stroke tool')

        N = struct.unpack(">i", fp.read(4))
        points = []
        for i in range(N[0]):
            x = struct.unpack(">f", fp.read(4))
            y = struct.unpack(">f", fp.read(4))
            p = struct.unpack(">f", fp.read(4))
            points.append((x[0], y[0], p[0]))

        return Stroke(thickness[0],red,green,blue,fountain_pen,points)

    def __init__(self,page_file,blob_loader):
        self.lines = []
        self.ovals = []
        self.triangles = []
        self.rectangles = []
        self.tables = []
        self.strokes = []
        self.images = []
        self.textboxes = []

        self._blob_loader = blob_loader
        print("These are info about the page\n")
        fp = self.fp = page_file
        self.version = struct.unpack(">i", fp.read(4))
        print(self.version)
        v = self.version[0]
        if v < 0 and v > 14:
            raise QuillImporterError('Wrong page version')
        #Handle all the version of the page
        if v == 2:
            self.paper_type = struct.unpack(">i", fp.read(4))
            foo = struct.unpack(">i", fp.read(4))
            foo = struct.unpack(">i", fp.read(4))
        elif v == 3:
            self.loadTagSet(fp)
            self.paper_type = struct.unpack(">i", fp.read(4))
            foo = struct.unpack(">i", fp.read(4))
            foo = struct.unpack(">i", fp.read(4))
        elif v == 4 or v == 5:
            nbytes = struct.unpack(">h", fp.read(2))
            self.uuid = fp.read(36)
            self.loadTagSet(fp)
            self.paper_type = struct.unpack(">i", fp.read(4))
            foo = struct.unpack(">i", fp.read(4))
            foo = struct.unpack(">i", fp.read(4))
        elif v >= 6:
            nbytes = struct.unpack(">h", fp.read(2))
            self.uuid = fp.read(36)
            self.loadTagSet(fp)
            self.paper_type = struct.unpack(">i", fp.read(4))
            if (v < 13):
                self.nimages = struct.unpack(">i", fp.read(4))
                self.images = [ self.read_image() for i in range(self.nimages[0]) ]
            foo = struct.unpack(">i", fp.read(4))

        if v < 13:
            self.read_only = struct.unpack(">?", fp.read(1))
            self.aspect_ratio = struct.unpack(">f", fp.read(4))[0]

            self.nstrokes = struct.unpack(">i", fp.read(4))
            self.strokes = [ self.read_stroke() for i in range(self.nstrokes[0]) ]

            if v >= 5:
                self.nlines = struct.unpack(">i", fp.read(4))
                self.lines = [ self.read_line() for i in range(self.nlines[0]) ]

                if v >= 8:
                    self.nRectangle = struct.unpack(">i", fp.read(4))
                    self.rectangles = [ self.read_rectangle() for i in range(self.nRectangle[0])]

                    if v >= 9:
                        self.nOval = struct.unpack(">i", fp.read(4))
                        self.ovals = [ self.read_oval() for i in range(self.nOval[0])]

                        self.nTriangle = struct.unpack(">i", fp.read(4))
                        self.triangles =  [ self.read_triangle() for i in range(self.nTriangle[0])]

                foo = struct.unpack(">i", fp.read(4))
                foo = struct.unpack(">i", fp.read(4)) #nText

                if v >= 7:
                    nbytes = struct.unpack(">h", fp.read(2))
                    self.paper_path = fp.read(nbytes[0]).decode("utf-8")

                    if v >= 10:
                        nbytes = struct.unpack(">h", fp.read(2))
                        self.mainTag = fp.read(nbytes[0]).decode("utf-8")

                        if v >= 11:
                            self.nTextBox = struct.unpack(">i", fp.read(4))
                            self.textboxes = [self.read_textbox() for i in range(self.nTextBox[0])]

                        if v >= 12:
                            self.nTable = struct.unpack(">i", fp.read(4))
                            self.tables = [self.read_table() for i in range(self.nTable[0])]

        else:
            self.read_only = struct.unpack(">?", fp.read(1))
            self.aspect_ratio = struct.unpack(">f", fp.read(4))[0]
            foo = struct.unpack(">i", fp.read(4))
            
            nbytes = struct.unpack(">h", fp.read(2))
            self.paper_path = fp.read(nbytes[0]).decode("utf-8")
            foo = struct.unpack(">i", fp.read(4))
            
            nbytes = struct.unpack(">h", fp.read(2))
            self.mainTag = fp.read(nbytes[0]).decode("utf-8")
            foo = struct.unpack(">i", fp.read(4))

            nbytes =  struct.unpack(">h", fp.read(2))
            self.timeStamp = fp.read(nbytes[0]).decode("utf-8")

            self.nTextBox = struct.unpack(">i", fp.read(4))
            self.textboxes = [self.read_textbox() for i in range(self.nTextBox[0])]

            if v >= 14:
                self.isRecognized = struct.unpack(">?", fp.read(1))
                self.ocr_version = struct.unpack(">i", fp.read(4))
                
                nbytes = struct.unpack(">h", fp.read(2))
                self.ocr_language = fp.read(nbytes[0]).decode("utf-8")

                nbytes = struct.unpack(">h", fp.read(2))
                self.ocr_textStr = fp.read(nbytes[0]).decode("utf-8")

                self.ocr_textFontSize = struct.unpack(">i", fp.read(4))
                self.ocr_isBold = struct.unpack(">?", fp.read(1))
                self.ocr_isItalic = struct.unpack(">?", fp.read(1))
                self.ocr_isUnderline = struct.unpack(">?", fp.read(1))

            self.loadPage_v13(fp)



