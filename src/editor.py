
PROGRAM_NAME = b'2D Model Editor'
PROGRAM_INFO = '''
*CONTROLS*

`[F1]` Help
`[F2]` Info
`[Tab]` Change mode (insert/edit/play)
`[~]` Toggle command line

`[Ctrl]+[Q]` Quit
`[Ctrl]+[N]` New model
`[Ctrl]+[O]` Open model
`[Ctrl]+[S]` Save model
`[Ctrl]+[B]` Export model to binary tree format
`[Ctrl]+[I]` Load image
`[Ctrl]+[V]` Change view mode (colored/outline/textured)
`[Ctrl]+[T]` Set texture coordinates for selected vertices
`[Ctrl]+[G]` Get color of the selected vertex
`[Ctrl]+[K]` Select color
`[Ctrl]+[Z]` Undo
`[Ctrl]+[0-9]` Select one of defined group of vertices

`[Ctrl]+[Shift]+[I]` Iterate over polygons
`[Ctrl]+[Shift]+[K]` Select background color
`[Ctrl]+[Shift]+[Z]` Redo
`[Ctrl]+[Shift]+[0-9]` Define a group of vertices

`[Ctrl]+[D]` Duplicate selected polygons
`[Ctrl]+[R]` Raise selected polygons to the top
`[Ctrl]+[L]` Lower selected polygons to the bottom
`[Ctrl]+[X]` Flip X coordinates
`[Ctrl]+[Y]` Flip Y coordinates

`[Delete]` Delete selected vertices
`[Shift]+[Delete]` Delete selected polygons

`[Insert]` New frame
`[Home]/[End]` Select previous/next animation
`[Page Up]/[Page Down]` Select previous/next frame

`[+]/[-]` Zoom in/out
Move mouse wheel to zoom in/out
Hold `[RMB]` and move mouse to move the camera

*INSERT MODE*

`[LMB]` New vertex
`[Esc]` Complete polygon creation

*EDIT MODE*

`[Esc]` Deselect
Hold `[LMB]` and move mouse to select vertices
Hold `[Ctrl]` and click `[LMB]` on a vertex to select/deselect it
Hold `[Shift]` and click `[LMB]` on a vertex to select entire polygon
Click and hold `[LMB]` on a vertex to move it
Click and hold `[LMB]` on a selected vertex to move all selected vertices
Hold `[R]+[LMB]` and move mouse to rotate selected vertices
Hold `[S]+[LMB]` and move mouse to scale selected vertices
Hold `[X]+[LMB]` and move mouse to scale selected vertices in X axis only
Hold `[Y]+[LMB]` and move mouse to scale selected vertices in Y axis only

*PLAY MODE*

`[<]/[>]` Decrease/increase FPS

*COMMAND LINE*

`[Enter]` Execute command
`[Backspace]` Delete last character
`[Up]/[Down]` Previous/next command history entry
`[Left]` Delete command
`[Right]` Complete command

*COMMANDS*

`quit`
Quit the editor.

`new`
Create a new model.

`open <file_path>`
Open model.

`save <file_path>`
Save model.

`btree <file_path>`
Export model to binary tree format.

`image <file_path>`
Load image.

`setcolor <red> <green> <blue> (<alpha>)`
Set color.

`setbgcolor <red> <green> <blue>`
Set background color.

`point (<point_name>)`
`edge (<edge_name>)`
`rect (<rectangle_name>)`
`circle (<circle_name>)`
Create a new point/edge/rectangle/circle of the specified name, or unnamed if no name is specified.

`anim (<animation_name>)`
Create a new animation of the specified name if it does not exist yet. The created or already existing animation is selected for edit.

`frame (<frame_num> (<animation_name>))`
Duplicate the specified frame, or the current frame if none is specified. The created frame is inserted after the current frame, and selected for edit.

`delanim (<animation_name>)`
Delete the specified animation, or the current animation if none is specified.

`delframe (<frame_num> (<animation_name>))`
Delete the specified frame, or the current frame if none is specified.

`goto <frame_num> (<animation_name>)`
Select the specified frame for edit.

`copyfrom <frame_num> (<animation_name>)`
Copy positions of the selected vertices from the specified frame to the current frame.
'''

MODEL_INFO_TEMPLATE = '''
Total number of triangles: {ntriangles}
Total number of polygons: {npolygons}
Total number of vertices: {nvertices}
Total number of frames: {nframes}

Animations: {animations}
Points: {points}
Edges: {edges}
Rectangles: {rectangles}
Circles: {circles}
'''

INIT_WINDOW_SIZE = (800, 600)
INIT_COLOR       = (1.0, 1.0, 1.0, 1.0)
INIT_BG_COLOR    = (0.5, 0.5, 0.5, 1.0)
INIT_FPS         = 1.0

TEXT_COLOR   = (1.0, 1.0, 1.0, 1.0)
ENTITY_COLOR = (1.0, 0.25, 0.0, 1.0)
VERTEX_COLOR = (1.0, 1.0, 0.0, 1.0)
SELECT_COLOR = (0.0, 1.0, 0.0, 1.0)

POINT_RADIUS  = 5
POINT_NVERTS  = 8
CIRCLE_NVERTS = 32
SELECT_DIST   = 10
UNDO_LEVELS   = 10

MODE_INSERT   = 'INSERT mode'
MODE_EDIT     = 'EDIT mode'
MODE_PLAY     = 'PLAY mode'
ENTITY_POINT  = 'point'
ENTITY_EDGE   = 'edge'
ENTITY_RECT   = 'rectangle'
ENTITY_CIRCLE = 'circle'
KEY_CTRL      = 'CTRL'
KEY_SHIFT     = 'SHIFT'
CMD_PREFIX    = '>>> '

VMODE_COLOR   = 0x1
VMODE_OUTLINE = 0x2
VMODE_TEXTURE = 0x4
VMODE_TEX_OUT = (VMODE_TEXTURE | VMODE_OUTLINE)

ENTITY_CONTAINERS = {
   ENTITY_POINT:  'points',
   ENTITY_EDGE:   'edges',
   ENTITY_RECT:   'rectangles',
   ENTITY_CIRCLE: 'circles'}

import copy, json, math, os, re, sys, time, traceback

try:
   import tkinter              as tk
   import tkinter.colorchooser as tkcolorchooser
   import tkinter.filedialog   as tkfiledialog
   import tkinter.messagebox   as tkmessagebox
   import tkinter.scrolledtext as tkscrolledtext
except ImportError:
   import Tkinter        as tk
   import tkColorChooser as tkcolorchooser
   import tkFileDialog   as tkfiledialog
   import tkMessageBox   as tkmessagebox
   import ScrolledText   as tkscrolledtext

try:
   get_time = time.perf_counter
except AttributeError:
   get_time = time.clock

from src.bindings import *
from src.btree import *

#===============================================================================

def show_message(title, message):

   def insert_message():
      buf = re.split(r'([*`])', message.strip())
      tag = None
      for item in buf:
         if item == '*':
            tag = None if tag else 'HEADER'
         elif item == '`':
            tag = None if tag else 'CODE'
         else:
            text.insert(tk.END, item, tag)

   def quit(event):
      top.destroy()

   top = tk.Toplevel()
   top.title(title)
   text = tkscrolledtext.ScrolledText(top, font = 'Calibri 11', wrap = tk.WORD)
   text.tag_config('HEADER', font = 'Calibri 14 bold')
   text.tag_config('CODE',   font = 'Consolas 11')
   text.bind('<Key-Escape>', quit)
   text.pack(expand = True, fill = tk.BOTH)
   text.focus_set()
   insert_message()
   text.config(state = tk.DISABLED)
   top.wait_window()

def stringify_tuples(obj):
   if isinstance(obj, tuple):
      return repr(obj)
   elif isinstance(obj, dict):
      return {key: stringify_tuples(val) for key, val in obj.items()}
   elif isinstance(obj, list):
      return [stringify_tuples(val) for val in obj]
   else:
      return obj

def dump_json(obj):
   obj = stringify_tuples(obj)
   s = json.dumps(obj, indent = 1, separators = (',', ': '), sort_keys = True)
   s = s.replace('"(', '[')
   s = s.replace(')"', ']')
   return s

def get_typed_char(char, shift, capslock):
   s1 = r"`1234567890-=[]\;',./"
   s2 = r'~!@#$%^&*()_+{}|:"<>?'
   if char.isalpha():
      if capslock:
         char = char.lower() if shift else char.upper()
      else:
         char = char.upper() if shift else char.lower()
   elif shift:
      ix = s1.find(char)
      if ix >= 0:
         char = s2[ix]
   return char

def rotate_vertex(vertex, origin, angle):
   sina = math.sin(angle)
   cosa = math.cos(angle)
   x, y = (vertex[0] - origin[0], vertex[1] - origin[1])
   x, y = (x*cosa - y*sina, x*sina + y*cosa)
   return (origin[0] + x, origin[1] + y)

def scale_vertex(vertex, origin, factor):
   x, y = (vertex[0] - origin[0], vertex[1] - origin[1])
   x, y = (x*factor, y*factor)
   return (origin[0] + x, origin[1] + y)

def load_texture(path):
   colormask = {
      'big'   : (0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF),
      'little': (0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)}
   tex = None
   ptr = IMG_Load(path.encode('utf-8'))
   if bool(ptr):
      surf = ptr.contents
      fmt = surf.format.contents
      rmask, gmask, bmask, amask = colormask[sys.byteorder]
      ptr = SDL_CreateRGBSurface(0, surf.w, surf.h, 32, rmask, gmask, bmask, amask)
      if bool(ptr):
         surf_ = ptr.contents
         SDL_UpperBlit(surf, None, surf_, None)
         tid = c_uint()
         glGenTextures(1, tid)
         glBindTexture(GL_TEXTURE_2D, tid)
         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
         glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, surf.w, surf.h, 0, GL_RGBA, GL_UNSIGNED_BYTE, surf_.pixels)
         tex = (tid, surf.w, surf.h)
         SDL_FreeSurface(surf_)
      SDL_FreeSurface(surf)
   return tex

def free_texture(tex):
   if tex is not None:
      glDeleteTextures(1, tex[0])

def set_texture(tex):
   if tex is None:
      glDisable(GL_TEXTURE_2D)
   else:
      glEnable(GL_TEXTURE_2D)
      glBindTexture(GL_TEXTURE_2D, tex[0]);
      glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

def draw_polygon(outline_color, vertices, colors, texcoords):
   if (colors is not None) or (texcoords is not None):
      ix = 0
      glBegin(GL_TRIANGLES)
      if colors is None:
         glColor4d(1,1,1,1)
      while ix < len(vertices):
         if colors is not None:
            r,g,b,a = colors[ix]
            glColor4d(r,g,b,a)
         if texcoords is not None:
            u,v = texcoords[ix]
            glTexCoord2d(u,v)
         x,y = vertices[ix]
         glVertex2d(x,y)
         ix += 1
      glEnd()
   if outline_color is not None:
      glColor4d(*outline_color)
      glBegin(GL_LINE_LOOP)
      for ix,(x,y) in enumerate(vertices):
         if (ix > 0) and ((ix % 3) == 0):
            glEnd()
            glBegin(GL_LINE_LOOP)
         glVertex2d(x,y)
      glEnd()

def draw_rect(color, outline_color, x1, y1, x2, y2):

   def put_vertices():
      glVertex2d(x1, y1)
      glVertex2d(x1, y2)
      glVertex2d(x2, y2)
      glVertex2d(x2, y1)

   if color is not None:
      glColor4d(*color)
      glBegin(GL_QUADS)
      put_vertices()
      glEnd()
   if outline_color is not None:
      glColor4d(*outline_color)
      glBegin(GL_LINE_LOOP)
      put_vertices()
      glEnd()

def draw_line(color, x1, y1, x2, y2):
   glColor4d(*color)
   glBegin(GL_LINES)
   glVertex2d(x1, y1)
   glVertex2d(x2, y2)
   glEnd()

def draw_point_square(color, x, y):
   glColor4d(*color)
   glBegin(GL_LINE_LOOP)
   glVertex2d(x-POINT_RADIUS, y-POINT_RADIUS)
   glVertex2d(x-POINT_RADIUS, y+POINT_RADIUS)
   glVertex2d(x+POINT_RADIUS, y+POINT_RADIUS)
   glVertex2d(x+POINT_RADIUS, y-POINT_RADIUS)
   glEnd()

def draw_circle(color, x, y, radius, num_vertices):
   angle = (2.0 * math.pi) / num_vertices
   sina = math.sin(angle)
   cosa = math.cos(angle)
   dx, dy = 0, -radius
   glColor4d(*color)
   glBegin(GL_LINE_LOOP)
   glVertex2d(x+dx, y+dy)
   for i in range(num_vertices-1):
      dx, dy = (dx*cosa - dy*sina, dx*sina + dy*cosa)
      glVertex2d(x+dx, y+dy)
   glEnd()

def draw_point_circle(color, x, y):
   draw_circle(color, x, y, POINT_RADIUS, POINT_NVERTS)

def draw_text(color, x, y, char_width, char_height, string):
   glColor4d(*color)
   glBegin(GL_QUADS)
   start_x = x
   for c in string:
      i = ord(c)
      if 32 <= i < 128:
         u = ((i - 32) % 16) / 16.0
         v = ((i - 32) // 16) / 6.0
         u_ = u + (1.0 / 16.0)
         v_ = v + (1.0 / 6.0)
         x_ = x + char_width
         y_ = y + char_height
         glTexCoord2d(u, v)
         glVertex2d(x, y)
         glTexCoord2d(u, v_)
         glVertex2d(x, y_)
         glTexCoord2d(u_, v_)
         glVertex2d(x_, y_)
         glTexCoord2d(u_, v)
         glVertex2d(x_, y)
      if c == '\n':
         x = start_x
         y = y_
      else:
         x = x_
   glEnd()

#===============================================================================

class CommandHistory:

   def __init__(self):
      self.data = ['']
      self.ix = 1

   def add(self, line):
      for ix, cmd in enumerate(self.data):
         if cmd == line:
            del self.data[ix]
            break
      self.data.append(line)
      self.ix = len(self.data)

   def getprev(self):
      self.ix = (self.ix - 1) if (self.ix > 0) else (len(self.data)-1)
      return self.data[self.ix]

   def getnext(self):
      self.ix = (self.ix + 1) if (self.ix < len(self.data)-1) else 0
      return self.data[self.ix]

#===============================================================================

class SnapshotHistory:

   def __init__(self, maxlen):
      self.maxlen = maxlen
      self.reset()

   def add(self, snapshot):
      self.history.append(snapshot)
      self.now_and_future = []
      if len(self.history) > self.maxlen:
         self.history = self.history[1:]

   def getprev(self, save_snapshot_fun):
      snapshot = None
      if self.history:
         snapshot = self.history[-1]
         if self.now_and_future:
            self.now_and_future = [snapshot] + self.now_and_future
         else:
            self.now_and_future = [snapshot, save_snapshot_fun()]
         self.history = self.history[:-1]
      return snapshot

   def getnext(self):
      snapshot = None
      if self.now_and_future:
         snapshot = self.now_and_future[1]
         self.history.append(self.now_and_future[0])
         if len(self.now_and_future) > 2:
            self.now_and_future = self.now_and_future[1:]
         else:
            self.now_and_future = []
      return snapshot

   def reset(self):
      self.history = []
      self.now_and_future = []

#===============================================================================

class RecoverableError(Exception):
   pass

class Application:

   def __init__(self):
      self.tk = tk.Tk()
      self.tk.withdraw() # Make the main Tkinter window hidden.
      self.reset_variables()
      self.exit = False
      self.mode = MODE_INSERT
      self.viewmode = VMODE_COLOR
      self.window_size = INIT_WINDOW_SIZE
      self.origin = (self.window_size[0]/2, self.window_size[1]/2)
      self.scale = (min(self.window_size) * 0.5, -min(self.window_size) * 0.5) # Flip Y axis.
      self.cur_color = INIT_COLOR
      self.bg_color = INIT_BG_COLOR
      self.mouse_pos = None
      self.mouse_pos_click = None
      self.frame_time = 0
      self.play_fps = INIT_FPS
      self.keys_pressed = set()
      self.font_tex = None
      self.font_glyph_size = (10,10)
      self.img_tex = None
      self.img_coords = None
      self.nearpoint_ix = -1
      self.selected_ix = -1
      self.select_rect = False
      self.cmd_line = ''
      self.cmd_history = CommandHistory()
      self.snapshot_history = SnapshotHistory(UNDO_LEVELS)
      self.snapshot_saved = False

   def run(self):
      self.image_formats_supported = IMG_Init(IMG_INIT_JPG | IMG_INIT_PNG | IMG_INIT_TIF)
      SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS)
      width, height = self.window_size
      self.wnd = SDL_CreateWindow(PROGRAM_NAME, SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, width, height, SDL_WINDOW_RESIZABLE | SDL_WINDOW_OPENGL)
      icon = IMG_Load(os.path.join('gfx', 'icon.tga').encode('utf-8'))
      SDL_SetWindowIcon(self.wnd, icon)
      SDL_FreeSurface(icon)
      self.ctx = SDL_GL_CreateContext(self.wnd)
      self.font_tex = load_texture(os.path.join('gfx', 'font.tga'))
      if self.font_tex is not None:
         self.font_glyph_size = (self.font_tex[1] / 16.0, self.font_tex[2] / 6.0)
      while not self.exit:
         if self.mode == MODE_PLAY:
            self.interpolate_vertices()
         self.render()
         evt = SDL_Event()
         try:
            if self.mode != MODE_PLAY:
               if SDL_WaitEvent(evt) > 0:
                  self.evt_main(evt)
            while SDL_PollEvent(evt) > 0:
               self.evt_main(evt)
         except RecoverableError as e:
            tkmessagebox.showerror('Runtime Error', str(e))
            self.back_from_other_window()
         except:
            tkmessagebox.showerror('Exception', traceback.format_exc())
            self.back_from_other_window()
      free_texture(self.font_tex)
      free_texture(self.img_tex)
      SDL_GL_DeleteContext(self.ctx)
      SDL_DestroyWindow(self.wnd)
      SDL_Quit()
      IMG_Quit()

   #============================================================================
   # Auxiliary functions.
   #============================================================================

   def back_from_other_window(self):
      self.keys_pressed -= set((KEY_CTRL, KEY_SHIFT)) # New window can steal CTRL/SHIFT key release.
      SDL_RaiseWindow(self.wnd)

   def reset_variables(self):
      self.selected = []
      self.selection_groups = [[] for ix in range(10)]
      self.anim_name = ''
      self.cur_frame = 0
      self.entities = [None]
      self.polygons = [None]
      self.colors = []
      self.texcoords = []
      self.vertices_anim = {self.anim_name: [[]]}
      self.vertices = self.vertices_anim[self.anim_name][self.cur_frame]

   def load_model(self, data):
      self.reset_variables()
      self.entities = []
      for ent_type, key in ENTITY_CONTAINERS.items():
         if key in data:
            for name, indices in data[key].items():
               self.entities += [([ent_type, name, ix] if (ent_type == ENTITY_POINT) else [ent_type, name] + list(ix)) for ix in indices]
      self.entities.append(None)
      self.polygons = [list(poly) for poly in data['polygons']] + [None]
      self.vertices_anim = data['vertices']
      for frames in self.vertices_anim.values():
         for ix in range(len(frames)):
            frames[ix] = [tuple(v) for v in frames[ix]]
      self.anim_name = sorted(self.vertices_anim.keys())[0]
      self.vertices = self.vertices_anim[self.anim_name][self.cur_frame]
      if ('colors' in data):
         self.colors = [tuple(c) for c in data['colors']]
      else:
         self.colors = [INIT_COLOR for v in self.vertices]
      if ('texcoords' in data):
         self.texcoords = [tuple(t) for t in data['texcoords']]
      else:
         self.texcoords = [(0,0) for v in self.vertices]

   def save_data_init(self, data):
      for dct_name in ENTITY_CONTAINERS.values():
         data[dct_name] = {}

   def save_data_cleanup(self, data):
      for dct_name in ENTITY_CONTAINERS.values():
         if len(data[dct_name]) == 0:
            del data[dct_name]
      if data['colors'].count(INIT_COLOR) == len(data['colors']):
         del data['colors']
      if data['texcoords'].count((0,0)) == len(data['texcoords']):
         del data['texcoords']

   def save_model(self):
      data = {
         'polygons':   [tuple(poly) for poly in self.polygons if poly],
         'colors':     self.colors,
         'texcoords':  self.texcoords,
         'vertices':   self.vertices_anim}
      self.save_data_init(data)
      for ent in self.entities:
         if ent and (len(ent) > 2):
            dct = data[ENTITY_CONTAINERS[ent[0]]]
            lst = dct[ent[1]] if ent[1] in dct else []
            val = tuple(ent[2:]) if (len(ent) > 3) else ent[2]
            lst.append(val)
            dct[ent[1]] = lst
      self.save_data_cleanup(data)
      return data

   def export_btree(self):
      data = BTreeBuilder().build(self.polygons, self.colors, self.texcoords, self.vertices)

      # Vertex array no longer contains vertices that are only used by entities
      # (i.e. they are not used by any polygon). We need to add them back.
      def find_vertex(index):
         if self.vertices[index] in data['vertices']:
            return data['vertices'].index(v)
         else:
            vix = len(data['vertices'])
            data['colors'].append(self.colors[index])
            data['texcoords'].append(self.texcoords[index])
            data['vertices'].append(self.vertices[index])
            return vix

      self.save_data_init(data)
      for ent in self.entities:
         if ent and (len(ent) > 2):
            dct = data[ENTITY_CONTAINERS[ent[0]]]
            lst = dct[ent[1]] if ent[1] in dct else []
            val = tuple([find_vertex(i) for i in ent[2:]]) if (len(ent) > 3) else find_vertex(ent[2])
            lst.append(val)
            dct[ent[1]] = lst
      self.save_data_cleanup(data)
      return data

   def load_snapshot(self, data):
      self.selected = copy.deepcopy(data['selected'])
      self.selection_groups = copy.deepcopy(data['selection_groups'])
      self.anim_name = data['anim_name']
      self.cur_frame = data['cur_frame']
      self.entities = copy.deepcopy(data['entities'])
      self.polygons = copy.deepcopy(data['polygons'])
      self.colors = copy.deepcopy(data['colors'])
      self.texcoords = copy.deepcopy(data['texcoords'])
      self.vertices_anim = copy.deepcopy(data['vertices_anim'])
      self.vertices = self.vertices_anim[self.anim_name][self.cur_frame]

   def save_snapshot(self):
      data = {
         'selected': copy.deepcopy(self.selected),
         'selection_groups': copy.deepcopy(self.selection_groups),
         'anim_name': self.anim_name,
         'cur_frame': self.cur_frame,
         'entities': copy.deepcopy(self.entities),
         'polygons': copy.deepcopy(self.polygons),
         'colors': copy.deepcopy(self.colors),
         'texcoords': copy.deepcopy(self.texcoords),
         'vertices_anim': copy.deepcopy(self.vertices_anim)}
      return data

   def restore_point(self):
      self.snapshot_history.add(self.save_snapshot())

   def undo_or_redo(self, shift_pressed):
      data = None
      if shift_pressed:
         data = self.snapshot_history.getnext()
      else:
         data = self.snapshot_history.getprev(self.save_snapshot)
      if data:
         self.load_snapshot(data)

   def transform_from_screen_coords(self, x, y):
      return ((x - self.origin[0]) / self.scale[0], (y - self.origin[1]) / self.scale[1])

   def transform_to_screen_coords(self, x, y):
      return (self.origin[0] + (x * self.scale[0]), self.origin[1] + (y * self.scale[1]))

   def vertex_to_screen_coords(self, ix):
      return self.transform_to_screen_coords(*self.vertices[ix])

   def find_nearby_vertex(self, x, y):
      result = (-1, 0, 0, 99999)
      for ix in range(len(self.vertices)):
         x_, y_ = self.vertex_to_screen_coords(ix)
         dx, dy = (x-x_, y-y_)
         dist_squared = dx*dx + dy*dy
         if dist_squared <= (SELECT_DIST * SELECT_DIST) and dist_squared < result[3]:
            result = (ix, int(x_), int(y_), dist_squared)
      return result[:3]

   def polygon_selected(self, poly):

      def all_vertices_selected(poly):
         for vix in poly:
            if vix not in self.selected:
               return False
         return True

      return (poly and all_vertices_selected(poly))

   def vertex_unused(self, index):
      for ent in self.entities:
         if ent and index in ent[2:]:
            return False
      for poly in self.polygons:
         if poly and index in poly:
            return False
      return True

   def reset_entity_or_polygon_creation(self):

      def delete_vertex(vertex_table, index2delete):
         del vertex_table[index2delete]

      if self.entities[-1]:
         indices = self.entities[-1][2:]
         self.entities[-1] = None
         for ix in reversed(indices):
            if self.vertex_unused(ix):
               self.foreach_vertex_table(delete_vertex, ix) # Guaranteed to be the last vertex.
               del self.colors[ix]
               del self.texcoords[ix]
      if self.polygons[-1]:
         indices = self.polygons[-1]
         if len(indices) < 3:
            self.polygons[-1] = None
            for ix in reversed(indices):
               if self.vertex_unused(ix):
                  self.foreach_vertex_table(delete_vertex, ix) # Guaranteed to be the last vertex.
                  del self.colors[ix]
                  del self.texcoords[ix]
         else:
            self.polygons.append(None)

   def new_selected(self, vertex_ix, invert):
      for ix, vix in enumerate(self.selected):
         if vix == vertex_ix:
            if invert:
               del self.selected[ix]
            return
      self.selected.append(vertex_ix)

   def foreach_vertex_table(self, fun, arg):
      for frame_table in self.vertices_anim.values():
         for vertex_table in frame_table:
            fun(vertex_table, arg)

   def delete_selected(self, whole_polygons_only):

      def delete_vertices(vertex_table, indices2delete):
         # Indices must be sorted in descending order here!
         for ix in indices2delete:
            del vertex_table[ix]

      def delete_colors_and_texcoords(indices2delete):
         # Indices must be sorted in descending order here!
         for ix in indices2delete:
            del self.colors[ix]
            del self.texcoords[ix]

      def create_index_map(indices2delete, nvertices):
         # Indices must be sorted in ascending order here!
         index_map = {}
         ix, di = 0,0
         while ix < nvertices:
            if ix in indices2delete:
               di -= 1
            else:
               index_map[ix] = ix + di
            ix += 1
         return index_map

      def update_selection_groups(index_map):
         for selection_group in self.selection_groups:
            ix = 0
            while ix < len(selection_group):
               vertex_ix = selection_group[ix]
               if selection_group[ix] in index_map:
                  selection_group[ix] = index_map[selection_group[ix]]
               else:
                  del selection_group[ix]
                  ix -= 1
               ix += 1

      def update_entities(index_map):
         indices2delete = set()
         ix = 0
         while ix < len(self.entities):
            ent = self.entities[ix]
            if ent:
               indices_old = ent[2:]
               indices_new = []
               for i in indices_old:
                  if i in index_map:
                     indices_new.append(index_map[i])
               if len(indices_new) == len(indices_old):
                  self.entities[ix] = ent[:2] + indices_new
               else:
                  if ix == len(self.entities)-1:
                     self.entities[ix] = None
                  else:
                     del self.entities[ix]
                     ix -= 1
                  for i in indices_new:
                     indices2delete.add(i)
            ix += 1
         return indices2delete

      def break_into_triples(poly):
         triples = []
         ix = 0
         while ix < len(poly):
            triples.append(poly[ix:ix+3])
            ix += 3
         return triples

      def update_polygons(index_map):
         indices2delete = set()
         ix = 0
         while ix < len(self.polygons):
            poly = self.polygons[ix]
            if poly:
               indices_old = break_into_triples(poly)
               indices_new = []
               for triple in indices_old:
                  if (len(triple) == 3) and (triple[0] in index_map) and (triple[1] in index_map) and (triple[2] in index_map):
                     for i in triple:
                        indices_new.append(index_map[i])
                  else:
                     for i in triple:
                        if i in index_map:
                           indices2delete.add(index_map[i])
               if len(indices_new) > 0:
                  self.polygons[ix] = indices_new
               else:
                  if ix == len(self.polygons)-1:
                     self.polygons[ix] = None
                  else:
                     del self.polygons[ix]
                     ix -= 1
            ix += 1
         return indices2delete

      def delete_selected_polygons():
         indices2delete = set()
         ix = 0
         while ix < len(self.polygons):
            poly = self.polygons[ix]
            if self.polygon_selected(poly):
               for i in poly:
                  indices2delete.add(i)
               del self.polygons[ix]
               ix -= 1
            ix += 1
         return [i for i in list(indices2delete) if self.vertex_unused(i)]

      indices = delete_selected_polygons() if whole_polygons_only else self.selected
      self.selected = []
      while indices:
         indices.sort()
         index_map = create_index_map(indices, len(self.vertices))
         indices.reverse()
         self.foreach_vertex_table(delete_vertices, indices)
         delete_colors_and_texcoords(indices)
         update_selection_groups(index_map)
         indices = list(update_entities(index_map) | update_polygons(index_map))
         indices = [i for i in indices if self.vertex_unused(i)]

   def new_entity(self, ent_type, ent_name):
      if self.entities[-1] is None:
         self.restore_point()
         self.entities[-1] = [ent_type, ent_name]
         self.set_mode(MODE_INSERT)

   def num_triangles(self):
      cnt = 0
      for poly in self.polygons:
         if poly:
            cnt += (len(poly) // 3)
      return cnt

   def num_polygons(self):
      cnt = len(self.polygons)
      return ((cnt-1) if (self.polygons[-1] is None) else cnt)

   def iterate_over_polygons(self):
      if self.num_polygons() > 0:
         selected_polygon_indices = [ix for ix, poly in enumerate(self.polygons) if self.polygon_selected(poly)]
         poly_ix = ((selected_polygon_indices[-1] + 1) % self.num_polygons()) if selected_polygon_indices else 0
         self.selected = []
         for ix in self.polygons[poly_ix]:
            self.new_selected(ix, False)

   def set_texcoords(self):
      x1,y1,x2,y2 = self.img_coords
      for vix in self.selected:
         x,y = self.vertex_to_screen_coords(vix)
         u = float(x-x1) / float(x2-x1)
         v = float(y-y1) / float(y2-y1)
         self.texcoords[vix] = (u,v)
      self.viewmode = VMODE_TEX_OUT

   def gather_color(self):
      if len(self.selected) > 0:
         self.cur_color = self.colors[self.selected[-1]]

   def duplicate_polygons(self):
      polygons = [poly for poly in self.polygons if self.polygon_selected(poly)]
      if polygons:
         dx = 10.0 / self.scale[0]
         dy = 10.0 / self.scale[1]
         index_map = {}
         for poly in polygons:
            for ix in poly:
               if ix not in index_map:
                  index_map[ix] = len(self.vertices)
                  x, y = self.vertices[ix]
                  self.foreach_vertex_table(lambda vtable, v: vtable.append(v), (x+dx, y+dy))
                  rgba = self.colors[ix]
                  self.colors.append(rgba)
                  uv = self.texcoords[ix]
                  self.texcoords.append(uv)
         for poly in polygons:
            new_poly = [index_map[ix] for ix in poly]
            self.polygons = self.polygons[:-1] + [new_poly] + self.polygons[-1:]
         self.selected = []
         for ix in index_map.values():
            self.new_selected(ix, False)

   def raise_selected_polygons(self):
      new_polygons = [[],[]]
      for poly in self.polygons:
         if self.polygon_selected(poly) or (poly is None):
            new_polygons[1].append(poly)
         else:
            new_polygons[0].append(poly)
      self.polygons = new_polygons[0] + new_polygons[1]

   def lower_selected_polygons(self):
      new_polygons = [[],[]]
      for poly in self.polygons:
         if self.polygon_selected(poly):
            new_polygons[0].append(poly)
         else:
            new_polygons[1].append(poly)
      self.polygons = new_polygons[0] + new_polygons[1]

   def flipx_selected_vertices(self):
      x_coords = [self.vertices[vix][0] for vix in self.selected]
      x_origin = (min(x_coords) + max(x_coords)) * 0.5
      for vix in self.selected:
         x, y = self.vertices[vix]
         self.vertices[vix] = (2.0 * x_origin - x, y)

   def flipy_selected_vertices(self):
      y_coords = [self.vertices[vix][1] for vix in self.selected]
      y_origin = (min(y_coords) + max(y_coords)) * 0.5
      for vix in self.selected:
         x, y = self.vertices[vix]
         self.vertices[vix] = (x, 2.0 * y_origin - y)

   def define_or_select_group(self, group_ix, define_group):
      if define_group:
         self.selection_groups[group_ix] = self.selected[:]
      else:
         self.selected = []
         for ix in self.selection_groups[group_ix]:
            self.new_selected(ix, False)

   def interpolate_vertices(self):
      frames = self.vertices_anim[self.anim_name]
      t = get_time()
      if len(frames) > 1:
         if self.frame_time > 0:
            dt = t - self.frame_time
            self.cur_frame += (dt * self.play_fps)
            if self.cur_frame > len(frames)-1:
               self.cur_frame = 0
         ix1 = int(self.cur_frame)
         ix2 = (ix1 + 1) % len(frames)
         delta = self.cur_frame - ix1
         self.vertices = [(x1+delta*(x2-x1), y1+delta*(y2-y1)) for (x1,y1),(x2,y2) in zip(frames[ix1], frames[ix2])]
      self.frame_time = t

   def get_info(self):

      def list2string(lst):
         lst.sort()
         return ', '.join(lst) if lst else '-'

      def entities_list(ent_type):
         lst = list(set([ent[1] for ent in self.entities if (ent and ent[1] and ent[0] == ent_type)]))
         return list2string(lst)

      return MODEL_INFO_TEMPLATE.format(
         ntriangles = self.num_triangles(),
         npolygons  = self.num_polygons(),
         nvertices  = len(self.vertices),
         nframes    = sum([len(frames) for frames in self.vertices_anim.values()]),
         animations = list2string(['{} ({})'.format(name, len(frames)) for name, frames in self.vertices_anim.items() if name]),
         points     = entities_list(ENTITY_POINT),
         edges      = entities_list(ENTITY_EDGE),
         rectangles = entities_list(ENTITY_RECT),
         circles    = entities_list(ENTITY_CIRCLE))

   def get_status_line_1(self):
      items = [self.mode]
      if self.mode == MODE_INSERT:
         msg = ''
         ent = self.entities[-1]
         if ent:
            if len(ent) == 2:
               msg = ' ({})'.format(ent[0])
            else:
               msg = ' (continue {})'.format(ent[0])
         elif self.polygons[-1]:
            msg = ' (continue)'
         items[0] = items[0] + msg
      if self.anim_name:
         items.append('animation: ' + self.anim_name)
      frame = self.cur_frame + 1
      nframes = len(self.vertices_anim[self.anim_name])
      if nframes > 1:
         if self.mode == MODE_PLAY:
            items.append('frame: %.3f/%d' % (frame, nframes))
            items.append('FPS: %.3f' % self.play_fps)
         else:
            items.append('frame: %d/%d' % (frame, nframes))
      return ', '.join(items)

   def get_status_line_2(self):
      descr = {
         VMODE_COLOR:   'Colored',
         VMODE_OUTLINE: 'Outline only',
         VMODE_TEX_OUT: 'Textured with outline',
         VMODE_TEXTURE: 'Textured'}
      return descr[self.viewmode]

   def get_position_line(self):
      x,y = (0,0)
      if self.nearpoint_ix >= 0:
         x,y = self.vertices[self.nearpoint_ix]
      else:
         x,y = self.transform_from_screen_coords(*self.mouse_pos)
      return ('X: %.5f, Y: %.5f' % (x,y))

   def set_mode(self, mode):
      if self.mode != mode:
         if self.mode == MODE_INSERT:
            self.reset_entity_or_polygon_creation()
         if self.mode == MODE_PLAY:
            self.cur_frame = int(self.cur_frame)
            self.vertices = self.vertices_anim[self.anim_name][self.cur_frame]
         self.mode = mode
         self.frame_time = 0

   def next_mode(self):
      change_table = {
         MODE_INSERT: MODE_EDIT,
         MODE_EDIT:   MODE_PLAY,
         MODE_PLAY:   MODE_INSERT}
      self.set_mode(change_table[self.mode])

   def next_viewmode(self):
      if self.img_tex is None:
         change_table = {
            VMODE_COLOR:   VMODE_OUTLINE,
            VMODE_OUTLINE: VMODE_COLOR,
            # These two should not happen if there is no image.
            VMODE_TEX_OUT: VMODE_COLOR,
            VMODE_TEXTURE: VMODE_COLOR}
         self.viewmode = change_table[self.viewmode]
      else:
         change_table = {
            VMODE_COLOR:   VMODE_OUTLINE,
            VMODE_OUTLINE: VMODE_TEX_OUT,
            VMODE_TEX_OUT: VMODE_TEXTURE,
            VMODE_TEXTURE: VMODE_COLOR}
         self.viewmode = change_table[self.viewmode]

   def prev_anim(self, anim_name):
      anim_names = sorted(self.vertices_anim.keys())
      for n in reversed(anim_names):
         if n < anim_name:
            return n
      return anim_names[-1]

   def next_anim(self, anim_name):
      anim_names = sorted(self.vertices_anim.keys())
      for n in anim_names:
         if n > anim_name:
            return n
      return anim_names[0]

   def execute_command(self, cmd):
      if cmd:
         self.cmd_line = ''
         self.cmd_history.add(cmd)
         cmd = cmd.split()
         fun = 'cmd_' + cmd[0]
         if fun not in self.__class__.__dict__:
            raise RecoverableError('Invalid command')
         self.__class__.__dict__[fun](self, *cmd[1:])

   def complete_command(self, cmd):
      if cmd:
         commands = [fun[4:] for fun in self.__class__.__dict__.keys() if fun.startswith('cmd_')]
         commands.sort()
         for command in commands:
            if command.startswith(cmd):
               self.cmd_line = CMD_PREFIX + command + ' '
               break

   def zoom(self, in_):
      f = 1.0625
      f = f if in_ else 1/f
      x = f * (self.origin[0] - self.window_size[0]/2) + self.window_size[0]/2
      y = f * (self.origin[1] - self.window_size[1]/2) + self.window_size[1]/2
      self.origin = (x, y)
      self.scale = (self.scale[0] * f, self.scale[1] * f)

   def calculate_image_coords(self):
      if self.img_tex is not None:
         img_w, img_h = self.img_tex[1:]
         wnd_w, wnd_h = self.window_size
         ratio_w = float(wnd_w) / float(img_w)
         ratio_h = float(wnd_h) / float(img_h)
         x1, y1 = 0,0
         x2, y2 = self.window_size
         if ratio_w > ratio_h:
            w = ratio_h * img_w
            x1 = (wnd_w - w) / 2
            x2 = x1 + w
         else:
            h = ratio_w * img_h
            y1 = (wnd_h - h) / 2
            y2 = y1 + h
         self.img_coords = (x1,y1,x2,y2)

   #============================================================================
   # Rendering.
   #============================================================================

   def pre_render(self):
      glViewport(0, 0, self.window_size[0], self.window_size[1])
      glMatrixMode(GL_PROJECTION)
      glLoadIdentity()
      glOrtho(0, self.window_size[0], self.window_size[1], 0, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      glClearColor(*self.bg_color)
      glClear(GL_COLOR_BUFFER_BIT)
      glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_BLEND)

   def post_render(self):
      SDL_GL_SwapWindow(self.wnd)

   def is_outofview(self, vertices):
      all_x = [x for (x,y) in vertices]
      all_y = [y for (x,y) in vertices]
      return (
         (max(all_x) <= 0) or (min(all_x) >= self.window_size[0]) or
         (max(all_y) <= 0) or (min(all_y) >= self.window_size[1]))

   def is_outofview2(self, x1, y1, x2, y2):
      return (
         (max(x1,x2) <= 0) or (min(x1,x2) >= self.window_size[0]) or
         (max(y1,y2) <= 0) or (min(y1,y2) >= self.window_size[1]))

   def is_outofview1(self, x, y):
      return (
         (x <= 0) or (x >= self.window_size[0]) or
         (y <= 0) or (y >= self.window_size[1]))

   def render_polygons(self):
      if (self.viewmode & VMODE_COLOR) != 0:
         for poly in self.polygons:
            if poly and len(poly) >= 3:
               vertices = [self.vertex_to_screen_coords(ix) for ix in poly]
               if not self.is_outofview(vertices):
                  colors = [self.colors[ix] for ix in poly]
                  draw_polygon(None, vertices, colors, None)
      if (self.viewmode & VMODE_TEXTURE) != 0:
         set_texture(self.img_tex)
         for poly in self.polygons:
            if poly and len(poly) >= 3:
               vertices = [self.vertex_to_screen_coords(ix) for ix in poly]
               if not self.is_outofview(vertices):
                  colors = [self.colors[ix] for ix in poly]
                  texcoords = [self.texcoords[ix] for ix in poly]
                  draw_polygon(None, vertices, colors, texcoords)
         set_texture(None)
      if (self.viewmode & VMODE_OUTLINE) != 0:
         for poly in self.polygons:
            if poly and len(poly) >= 3:
               vertices = [self.vertex_to_screen_coords(ix) for ix in poly]
               if not self.is_outofview(vertices):
                  draw_polygon(VERTEX_COLOR, vertices, None, None)
      if self.polygons[-1]:
         poly = self.polygons[-1]
         vertices = [self.vertex_to_screen_coords(ix) for ix in poly[-2:]]
         for x,y in vertices:
            if not self.is_outofview1(x, y):
               draw_point_circle(VERTEX_COLOR, x, y)

   def render_entities(self):
      for ent in self.entities:
         if ent and len(ent) >= 3:
            x1,y1 = self.vertex_to_screen_coords(ent[2])
            hidden = True
            if len(ent) == 3: # Point or incomplete edge/rectangle/circle.
               if not self.is_outofview1(x1, y1):
                  hidden = False
                  if ent[0] == ENTITY_RECT:
                     draw_point_square(ENTITY_COLOR, x1, y1)
                  else:
                     draw_point_circle(ENTITY_COLOR, x1, y1)
            elif ent[0] == ENTITY_CIRCLE:
               x2,y2 = self.vertex_to_screen_coords(ent[3])
               radius = math.sqrt((x1-x2)**2 + (y1-y2)**2)
               if not self.is_outofview2(x1-radius, y1-radius, x1+radius, y1+radius):
                  hidden = False
                  draw_circle(ENTITY_COLOR, x1, y1, radius, CIRCLE_NVERTS)
                  draw_line(ENTITY_COLOR, x1, y1, x2, y2)
            else:
               x2,y2 = self.vertex_to_screen_coords(ent[3])
               if not self.is_outofview2(x1, y1, x2, y2):
                  hidden = False
                  if ent[0] == ENTITY_EDGE:
                     draw_line(ENTITY_COLOR, x1, y1, x2, y2)
                  elif ent[0] == ENTITY_RECT:
                     draw_rect(None, ENTITY_COLOR, x1, y1, x2, y2)
            if not hidden and ent[1]:
               set_texture(self.font_tex)
               ch_w, ch_h = self.font_glyph_size
               draw_text(ENTITY_COLOR, x1, y1, ch_w, ch_h, ent[1])
               set_texture(None)

   def render(self):
      self.pre_render()
      if (self.viewmode & VMODE_TEXTURE) == 0 and self.img_tex is not None:
         set_texture(self.img_tex)
         x1,y1,x2,y2 = self.img_coords
         draw_polygon(None, ((x1,y1),(x1,y2),(x2,y2),(x1,y1),(x2,y2),(x2,y1)), None, ((0,0),(0,1),(1,1),(0,0),(1,1),(1,0)))
      set_texture(None)
      self.render_polygons()
      self.render_entities()
      for vix in self.selected:
         x,y = self.vertex_to_screen_coords(vix)
         if not self.is_outofview1(x, y):
            draw_point_circle(SELECT_COLOR, x, y)
      if self.select_rect:
         x,y = self.mouse_pos
         draw_rect(None, SELECT_COLOR, x, y, *self.mouse_pos_click)
      if self.mouse_pos is not None:
         self.nearpoint_ix, x, y = self.find_nearby_vertex(*self.mouse_pos)
         if self.nearpoint_ix >= 0:
            draw_point_circle(VERTEX_COLOR, x, y)
      draw_rect(self.cur_color, TEXT_COLOR, 5, 5, 45, 45)
      set_texture(self.font_tex)
      ch_w, ch_h = self.font_glyph_size
      draw_text(TEXT_COLOR, 50, 5,      ch_w, ch_h, self.get_status_line_1())
      draw_text(TEXT_COLOR, 50, 5+ch_h, ch_w, ch_h, self.get_status_line_2())
      if self.mouse_pos is not None:
         draw_text(TEXT_COLOR, 50, 5+2*ch_h, ch_w, ch_h, self.get_position_line())
      if self.cmd_line:
         draw_text(TEXT_COLOR, 0, self.window_size[1]-ch_h, ch_w, ch_h, self.cmd_line)
      self.post_render()

   #============================================================================
   # Event handlers.
   #============================================================================

   def evt_main(self, event):
      if event.type == SDL_QUIT:
         self.exit = True
      elif event.type == SDL_WINDOWEVENT:
         if event.window.event in (SDL_WINDOWEVENT_RESIZED, SDL_WINDOWEVENT_SIZE_CHANGED):
            self.evt_resize(event.window)
      elif event.type == SDL_KEYDOWN:
         self.evt_key(event.key)
      elif event.type == SDL_KEYUP:
         self.evt_key_release(event.key)
      elif event.type == SDL_MOUSEBUTTONDOWN:
         if event.button.button == SDL_BUTTON_LEFT:
            self.evt_b1(event.button)
      elif event.type == SDL_MOUSEBUTTONUP:
         if event.button.button == SDL_BUTTON_LEFT:
            self.evt_b1_release(event.button)
      elif event.type == SDL_MOUSEMOTION:
         if (event.motion.state & SDL_BUTTON_LMASK) != 0:
            self.evt_motion_b1(event.motion)
         elif (event.motion.state & (SDL_BUTTON_MMASK | SDL_BUTTON_RMASK)) != 0:
            self.evt_motion_b2_b3(event.motion)
         else:
            self.evt_motion(event.motion)
      elif event.type == SDL_MOUSEWHEEL:
         self.evt_wheel(event.wheel)

   def evt_resize(self, event):
      prev_window_size = self.window_size
      self.window_size = (event.data1, event.data2)
      dx = (self.window_size[0] - prev_window_size[0]) / 2
      dy = (self.window_size[1] - prev_window_size[1]) / 2
      self.origin = (self.origin[0] + dx, self.origin[1] + dy)
      self.calculate_image_coords()

   def evt_update_ctrl_shift(self, event):
      def update(mask, key):
         if (event.keysym.mod & mask) != 0:
            self.keys_pressed.add(key)
         elif key in self.keys_pressed:
            self.keys_pressed.remove(key)
      update(KMOD_CTRL, KEY_CTRL)
      update(KMOD_SHIFT, KEY_SHIFT)

   def evt_get_image_path(self):
      formats = ['.bmp', '.gif', '.tga']
      if (self.image_formats_supported & IMG_INIT_JPG) != 0: formats += ['.jpg', '.jpeg']
      if (self.image_formats_supported & IMG_INIT_PNG) != 0: formats += ['.png']
      if (self.image_formats_supported & IMG_INIT_TIF) != 0: formats += ['.tif', '.tiff']
      path = tkfiledialog.askopenfilename(title = 'Open', filetypes = (('Image files', tuple(sorted(formats))), ('All files', '.*')))
      self.back_from_other_window()
      return path

   def evt_key(self, event):
      self.evt_update_ctrl_shift(event)
      ctrl = (KEY_CTRL in self.keys_pressed)
      shift = (KEY_SHIFT in self.keys_pressed)
      sym = event.keysym.sym
      char = chr(sym).upper() if (32 <= sym < 128) else None
      if sym == SDLK_F1:
         show_message('Help', PROGRAM_INFO)
      elif sym == SDLK_F2:
         show_message('Info', self.get_info())
      elif sym == SDLK_TAB:
         self.next_mode()
      elif sym == SDLK_INSERT:
         self.cmd_frame()
      elif sym == SDLK_DELETE:
         self.restore_point()
         self.delete_selected(shift)
      elif sym == SDLK_HOME:
         if len(self.vertices_anim) > 1:
            self.cmd_goto(1, self.prev_anim(self.anim_name))
      elif sym == SDLK_END:
         if len(self.vertices_anim) > 1:
            self.cmd_goto(1, self.next_anim(self.anim_name))
      elif sym == SDLK_PAGEUP:
         self.cmd_goto(((self.cur_frame-1) % len(self.vertices_anim[self.anim_name])) + 1)
      elif sym == SDLK_PAGEDOWN:
         self.cmd_goto(((self.cur_frame+1) % len(self.vertices_anim[self.anim_name])) + 1)
      elif sym == SDLK_ESCAPE:
         self.selected = []
         self.reset_entity_or_polygon_creation()
      elif ctrl and char == 'Q':
         if tkmessagebox.askyesno('Confirmation', 'Do you really want to quit?'):
            self.cmd_quit()
         self.back_from_other_window()
      elif ctrl and char == 'N':
         if tkmessagebox.askyesno('Confirmation', 'Do you really want to start new model?'):
            self.cmd_new()
         self.back_from_other_window()
      elif ctrl and char == 'O':
         path = tkfiledialog.askopenfilename(title = 'Open', defaultextension = '.json', filetypes = (('Json files', '.json'), ('All files', '.*')))
         self.back_from_other_window()
         if path:
            self.cmd_open(path)
      elif ctrl and char == 'S':
         path = tkfiledialog.asksaveasfilename(title = 'Save', defaultextension = '.json', filetypes = (('Json files', '.json'), ('All files', '.*')))
         self.back_from_other_window()
         if path:
            self.cmd_save(path)
      elif ctrl and char == 'B':
         path = tkfiledialog.asksaveasfilename(title = 'Export', defaultextension = '.json', filetypes = (('Json files', '.json'), ('All files', '.*')))
         self.back_from_other_window()
         if path:
            self.cmd_btree(path)
      elif ctrl and char == 'I':
         if shift:
            self.iterate_over_polygons()
         else:
            path = self.evt_get_image_path()
            if path:
               self.cmd_image(path)
      elif ctrl and char == 'V':
         self.next_viewmode()
      elif ctrl and char == 'T':
         self.set_texcoords()
      elif ctrl and char == 'G':
         self.gather_color()
      elif ctrl and char == 'K':
         initcolor = tuple([int(color_component * 255.0) for color_component in self.cur_color[:3]])
         triple, color = tkcolorchooser.askcolor(initcolor, title = 'Select color')
         self.back_from_other_window()
         if triple:
            triple = [color_component / 255.0 for color_component in triple]
            if shift:
               self.cmd_setbgcolor(*triple)
            else:
               self.cmd_setcolor(*triple)
      elif ctrl and char == 'Z':
         self.undo_or_redo(shift)
      elif ctrl and char == 'D':
         self.restore_point()
         self.duplicate_polygons()
      elif ctrl and char == 'R':
         self.restore_point()
         self.raise_selected_polygons()
      elif ctrl and char == 'L':
         self.restore_point()
         self.lower_selected_polygons()
      elif ctrl and char == 'X':
         self.restore_point()
         self.flipx_selected_vertices()
      elif ctrl and char == 'Y':
         self.restore_point()
         self.flipy_selected_vertices()
      elif ctrl and char is not None and char.isdigit():
         self.define_or_select_group(int(char), shift)
      elif self.cmd_line == '':
         if char in ('`','~'):
            self.cmd_line = CMD_PREFIX
         elif char in ('-','_'):
            self.zoom(False)
         elif char in ('=','+'):
            self.zoom(True)
         elif char in (',','<'):
            self.play_fps *= (1.0 / 1.25)
         elif char in ('.','>'):
            self.play_fps *= 1.25
         elif char is not None and char.isalpha():
            self.keys_pressed.add(char)
      else:
         cmd = self.cmd_line[len(CMD_PREFIX):]
         if char in ('`','~'):
            self.cmd_line = ''
         elif sym == SDLK_BACKSPACE:
            self.cmd_line = CMD_PREFIX + cmd[:-1]
         elif sym == SDLK_RETURN:
            self.execute_command(cmd)
         elif sym == SDLK_RIGHT:
            self.complete_command(cmd)
         elif sym == SDLK_LEFT:
            self.cmd_line = CMD_PREFIX
         elif sym == SDLK_UP:
            self.cmd_line = CMD_PREFIX + self.cmd_history.getprev()
         elif sym == SDLK_DOWN:
            self.cmd_line = CMD_PREFIX + self.cmd_history.getnext()
         elif char is not None:
            self.cmd_line = CMD_PREFIX + cmd + get_typed_char(char, shift, ((event.keysym.mod & KMOD_CAPS) != 0))

   def evt_key_release(self, event):
      self.evt_update_ctrl_shift(event)
      sym = event.keysym.sym
      char = chr(sym).upper() if (32 <= sym < 128) else None
      if char in self.keys_pressed:
         self.keys_pressed.remove(char)

   def evt_b1(self, event):
      self.snapshot_saved = False
      self.selected_ix = -1
      self.mouse_pos_click = (event.x, event.y)
      if self.mode == MODE_INSERT:
         self.restore_point()
         vertex_ix = self.nearpoint_ix
         if vertex_ix < 0:
            vertex_ix = len(self.vertices)
            vertex = self.transform_from_screen_coords(event.x, event.y)
            self.foreach_vertex_table(lambda vtable, v: vtable.append(v), vertex)
            self.colors.append(self.cur_color)
            self.texcoords.append((0,0))
         ent = self.entities[-1]
         if ent and ent[0] == ENTITY_POINT and len(ent) < 3:
            ent.append(vertex_ix)
            self.entities.append(None)
            self.new_entity(ent[0], ent[1])
         elif ent and ent[0] in (ENTITY_EDGE, ENTITY_RECT, ENTITY_CIRCLE) and len(ent) < 4:
            ent.append(vertex_ix)
            if len(ent) == 4:
               self.entities.append(None)
               self.new_entity(ent[0], ent[1])
         elif self.polygons[-1]:
            poly = self.polygons[-1]
            if len(poly) >= 3:
               poly += poly[-2:]
            poly.append(vertex_ix)
         else:
            self.polygons[-1] = [vertex_ix]
      elif self.mode == MODE_EDIT and self.nearpoint_ix >= 0:
         self.selected_ix = self.nearpoint_ix
         if KEY_SHIFT in self.keys_pressed:
            for poly in self.polygons:
               if poly and self.selected_ix in poly:
                  for ix in poly:
                     self.new_selected(ix, (KEY_CTRL in self.keys_pressed))
         elif KEY_CTRL in self.keys_pressed:
            self.new_selected(self.selected_ix, True)

   def evt_b1_release(self, event):
      self.snapshot_saved = False
      self.selected_ix = -1
      if self.select_rect:
         self.select_rect = False
         if self.mode == MODE_EDIT:
            x1, y1 = self.transform_from_screen_coords(*self.mouse_pos_click)
            x2, y2 = self.transform_from_screen_coords(event.x, event.y)
            left, right = (x1, x2) if (x1 < x2) else (x2, x1)
            top, bottom = (y1, y2) if (y1 < y2) else (y2, y1)
            for ix, (x, y) in enumerate(self.vertices):
               if x >= left and x <= right and y >= top and y <= bottom:
                  self.new_selected(ix, (KEY_CTRL in self.keys_pressed))

   def evt_motion(self, event):
      self.mouse_pos = (event.x, event.y)

   def evt_motion_b1(self, event):

      def scale_factor(dx, dy):
         f = 4.0 * (float(dx + dy) / sum(self.window_size))
         return (0.25*f*f + 0.75*f + 1.0) # [-1..0..1] => [0.5..1..2]

      def possible_restore_point():
         if self.snapshot_saved == False:
            self.snapshot_saved = True
            self.restore_point()

      dx = (event.x - self.mouse_pos[0]) * math.copysign(1.0, self.scale[0])
      dy = (event.y - self.mouse_pos[1]) * math.copysign(1.0, self.scale[1])
      self.mouse_pos = (event.x, event.y)
      if self.mode == MODE_EDIT:
         origin = self.transform_from_screen_coords(*self.mouse_pos_click)
         if self.selected and 'R' in self.keys_pressed:
            possible_restore_point()
            angle = 4.0 * math.pi * (float(dx + dy) / sum(self.window_size))
            for vix in self.selected:
               self.vertices[vix] = rotate_vertex(self.vertices[vix], origin, angle)
         elif self.selected and 'S' in self.keys_pressed:
            possible_restore_point()
            for vix in self.selected:
               self.vertices[vix] = scale_vertex(self.vertices[vix], origin, scale_factor(dx, dy))
         elif self.selected and 'X' in self.keys_pressed:
            possible_restore_point()
            for vix in self.selected:
               vertex_old = self.vertices[vix]
               vertex_new = scale_vertex(vertex_old, origin, scale_factor(dx, dy))
               self.vertices[vix] = (vertex_new[0], vertex_old[1])
         elif self.selected and 'Y' in self.keys_pressed:
            possible_restore_point()
            for vix in self.selected:
               vertex_old = self.vertices[vix]
               vertex_new = scale_vertex(vertex_old, origin, scale_factor(dx, dy))
               self.vertices[vix] = (vertex_old[0], vertex_new[1])
         elif self.selected_ix >= 0 and self.selected_ix in self.selected:
            possible_restore_point()
            for vix in self.selected:
               x, y = self.vertices[vix]
               self.vertices[vix] = (x + dx / abs(self.scale[0]), y + dy / abs(self.scale[1]))
         elif self.selected_ix >= 0:
            possible_restore_point()
            self.vertices[self.selected_ix] = self.transform_from_screen_coords(event.x, event.y)
         else:
            self.select_rect = True

   def evt_motion_b2_b3(self, event):
      dx = event.x - self.mouse_pos[0]
      dy = event.y - self.mouse_pos[1]
      self.mouse_pos = (event.x, event.y)
      self.origin = (self.origin[0] + dx, self.origin[1] + dy)

   def evt_wheel(self, event):
      self.zoom(event.y > 0)

   #============================================================================
   # Command handlers.
   #============================================================================

   def cmd_quit(self, *args):
      self.exit = True

   def cmd_new(self, *args):
      self.snapshot_history.reset()
      self.reset_variables()
      self.set_mode(MODE_INSERT)

   def cmd_open(self, *args):
      if len(args) < 1:
         raise RecoverableError('Syntax: open <file_path>')
      self.snapshot_history.reset()
      data = None
      try:
         with open(args[0], 'r') as f:
            data = json.load(f)
      except:
         raise RecoverableError('Read failure')
      try:
         self.load_model(data)
      except:
         self.cmd_new()
         raise RecoverableError('Invalid format')

   def cmd_save(self, *args):
      if len(args) < 1:
         raise RecoverableError('Syntax: save <file_path>')
      data = dump_json(self.save_model())
      try:
         with open(args[0], 'w') as f:
            f.write(data)
      except:
         raise RecoverableError('Write failure')

   def cmd_btree(self, *args):
      if len(args) < 1:
         raise RecoverableError('Syntax: btree <file_path>')
      data = dump_json(self.export_btree())
      try:
         with open(args[0], 'w') as f:
            f.write(data)
      except:
         raise RecoverableError('Write failure')

   def cmd_image(self, *args):
      free_texture(self.img_tex)
      self.img_tex = None
      self.img_coords = None
      if len(args) >= 1:
         try:
            self.img_tex = load_texture(args[0])
            self.calculate_image_coords()
         except:
            raise RecoverableError('Read failure')
      if self.img_tex is None:
         # Not every view mode is valid if there is no image.
         if self.viewmode != VMODE_COLOR and self.viewmode != VMODE_OUTLINE:
            self.viewmode = VMODE_COLOR

   def cmd_setcolor(self, *args):
      if len(args) < 3:
         raise RecoverableError('Syntax: setcolor <red> <green> <blue> (<alpha>)')
      r,g,b,a = 0,0,0,0
      try:
         r = min(max(float(args[0]), 0.0), 1.0)
         g = min(max(float(args[1]), 0.0), 1.0)
         b = min(max(float(args[2]), 0.0), 1.0)
         a = min(max(float(args[3]), 0.0), 1.0) if (len(args) >= 4) else 1.0
      except:
         raise RecoverableError('Invalid value')
      self.cur_color = (r, g, b, a)
      snapshot_saved = False
      for ix in self.selected:
         if snapshot_saved == False:
            snapshot_saved = True
            self.restore_point()
         self.colors[ix] = self.cur_color

   def cmd_setbgcolor(self, *args):
      if len(args) < 3:
         raise RecoverableError('Syntax: setbgcolor <red> <green> <blue>')
      r,g,b = 0,0,0
      try:
         r = min(max(float(args[0]), 0.0), 1.0)
         g = min(max(float(args[1]), 0.0), 1.0)
         b = min(max(float(args[2]), 0.0), 1.0)
      except:
         raise RecoverableError('Invalid value')
      self.bg_color = (r, g, b, 1.0)

   def cmd_point(self, *args):
      self.reset_entity_or_polygon_creation()
      self.new_entity(ENTITY_POINT, (args[0] if (len(args) > 0) else ''))

   def cmd_edge(self, *args):
      self.reset_entity_or_polygon_creation()
      self.new_entity(ENTITY_EDGE, (args[0] if (len(args) > 0) else ''))

   def cmd_rect(self, *args):
      self.reset_entity_or_polygon_creation()
      self.new_entity(ENTITY_RECT, (args[0] if (len(args) > 0) else ''))

   def cmd_circle(self, *args):
      self.reset_entity_or_polygon_creation()
      self.new_entity(ENTITY_CIRCLE, (args[0] if (len(args) > 0) else ''))

   def cmd_anim(self, *args):
      self.set_mode(MODE_EDIT)
      anim_name = args[0] if (len(args) >= 1) else ''
      if anim_name != self.anim_name:
         if anim_name not in self.vertices_anim:
            self.restore_point()
         self.anim_name = anim_name
         self.cur_frame = 0
         if self.anim_name not in self.vertices_anim:
            self.vertices = self.vertices[:]
            self.vertices_anim[self.anim_name] = [self.vertices]
         else:
            self.vertices = self.vertices_anim[self.anim_name][self.cur_frame]

   def cmd_delanim(self, *args):
      anim_name = args[0] if (len(args) >= 1) else self.anim_name
      if anim_name not in self.vertices_anim:
         raise RecoverableError('No animation')
      if len(self.vertices_anim) == 1:
         raise RecoverableError('Invalid operation')
      self.restore_point()
      del self.vertices_anim[anim_name]
      if self.anim_name == anim_name:
         self.cmd_goto(1, self.next_anim(anim_name))

   def cmd_frame(self, *args):
      if self.mode == MODE_PLAY:
         raise RecoverableError('Invalid mode')
      frame_ix  = int(args[0])-1 if (len(args) >= 1) else self.cur_frame
      anim_name =     args[1]    if (len(args) >= 2) else self.anim_name
      if anim_name not in self.vertices_anim:
         raise RecoverableError('No animation')
      if (frame_ix < 0) or (frame_ix >= len(self.vertices_anim[anim_name])):
         raise RecoverableError('No frame')
      self.restore_point()
      self.vertices = self.vertices_anim[anim_name][frame_ix][:]
      self.cur_frame += 1
      allframes = self.vertices_anim[self.anim_name]
      self.vertices_anim[self.anim_name] = allframes[:self.cur_frame] + [self.vertices] + allframes[self.cur_frame:]

   def cmd_delframe(self, *args):
      if self.mode == MODE_PLAY:
         raise RecoverableError('Invalid mode')
      frame_ix  = int(args[0])-1 if (len(args) >= 1) else self.cur_frame
      anim_name =     args[1]    if (len(args) >= 2) else self.anim_name
      if anim_name not in self.vertices_anim:
         raise RecoverableError('No animation')
      if (frame_ix < 0) or (frame_ix >= len(self.vertices_anim[anim_name])):
         raise RecoverableError('No frame')
      if len(self.vertices_anim[anim_name]) == 1:
         self.cmd_delanim(anim_name)
      else:
         self.restore_point()
         del self.vertices_anim[anim_name][frame_ix]
         if self.anim_name == anim_name:
            self.cur_frame = min(self.cur_frame, len(self.vertices_anim[self.anim_name])-1)
            self.vertices = self.vertices_anim[self.anim_name][self.cur_frame]

   def cmd_goto(self, *args):
      if len(args) < 1:
         raise RecoverableError('Syntax: goto <frame_num> (<animation_name>)')
      frame_ix = int(args[0])-1
      anim_name = args[1] if len(args) > 1 else self.anim_name
      if anim_name not in self.vertices_anim:
         raise RecoverableError('No animation')
      if frame_ix >= len(self.vertices_anim[anim_name]):
         raise RecoverableError('No frame')
      # Makes no sense to change frame in play mode, unless when jumping to another animation.
      if (self.mode != MODE_PLAY) or (self.anim_name != anim_name):
         self.anim_name = anim_name
         self.cur_frame = frame_ix
         self.vertices = self.vertices_anim[self.anim_name][self.cur_frame]

   def cmd_copyfrom(self, *args):
      if self.mode == MODE_PLAY:
         raise RecoverableError('Invalid mode')
      if len(args) < 1:
         raise RecoverableError('Syntax: copyfrom <frame_num> (<animation_name>)')
      frame_ix = int(args[0])-1
      anim_name = args[1] if len(args) > 1 else self.anim_name
      if anim_name not in self.vertices_anim:
         raise RecoverableError('No animation')
      if frame_ix >= len(self.vertices_anim[anim_name]):
         raise RecoverableError('No frame')
      self.restore_point()
      for vix in self.selected:
         x, y = self.vertices_anim[anim_name][frame_ix][vix]
         self.vertices[vix] = (x, y)
