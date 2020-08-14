
from ctypes import c_char_p, c_double, c_float, c_int, c_ubyte, c_uint, c_ushort, c_void_p
from ctypes import POINTER, Structure, Union

#===============================================================================
# Helper function to load libraries and functions.
#===============================================================================

_libraries = {}

def _load(lib_name, fun_name, res_type, arg_types):
   import ctypes, ctypes.util, os, sys
   if lib_name not in _libraries:
      is_win = sys.platform.startswith('win')
      if is_win and (lib_name == 'GL'):
         _libraries[lib_name] = ctypes.windll.LoadLibrary(ctypes.util.find_library('opengl32'))
      else:
         if is_win:
            lib_path = os.path.join(os.getcwd(), 'lib')
            os.environ['PATH'] = ';'.join([os.environ['PATH'], lib_path])
         _libraries[lib_name] = ctypes.cdll.LoadLibrary(ctypes.util.find_library(lib_name))
   fun = None
   lib = _libraries[lib_name]
   if lib is not None:
      fun = getattr(lib, fun_name)
      fun.argtypes = arg_types
      fun.restype = res_type
   globals()[fun_name] = fun

#===============================================================================
# SDL and SDL_image bindings.
#===============================================================================

class SDL_Rect(Structure):
   _fields_ = [
      ('x', c_int),
      ('y', c_int),
      ('w', c_int),
      ('h', c_int)]

class SDL_PixelFormat(Structure):
   _fields_ = [
      ('format',        c_uint),
      ('palette',       c_void_p),
      ('BitsPerPixel',  c_ubyte),
      ('BytesPerPixel', c_ubyte),
      ('padding',       c_ubyte * 2),
      ('Rmask',         c_uint),
      ('Gmask',         c_uint),
      ('Bmask',         c_uint),
      ('Amask',         c_uint),
      ('Rloss',         c_ubyte),
      ('Gloss',         c_ubyte),
      ('Bloss',         c_ubyte),
      ('Aloss',         c_ubyte),
      ('Rshift',        c_ubyte),
      ('Gshift',        c_ubyte),
      ('Bshift',        c_ubyte),
      ('Ashift',        c_ubyte),
      ('refcount',      c_int),
      ('next',          c_void_p)]

class SDL_Surface(Structure):
   _fields_ = [
      ('flags',     c_uint),
      ('format',    POINTER(SDL_PixelFormat)),
      ('w',         c_int),
      ('h',         c_int),
      ('pitch',     c_int),
      ('pixels',    c_void_p),
      ('userdata',  c_void_p),
      ('locked',    c_int),
      ('lock_data', c_void_p),
      ('clip_rect', SDL_Rect),
      ('map',       c_void_p),
      ('refcount',  c_int)]

class SDL_WindowEvent(Structure):
   _fields_ = [
      ('type',      c_uint),
      ('timestamp', c_uint),
      ('windowID',  c_uint),
      ('event',     c_ubyte),
      ('padding',   c_ubyte * 3),
      ('data1',     c_int),
      ('data2',     c_int)]

class SDL_Keysym(Structure):
   _fields_ = [
      ('scancode', c_int),
      ('sym',      c_int),
      ('mod',      c_ushort),
      ('unused',   c_uint)]

class SDL_KeyboardEvent(Structure):
   _fields_ = [
      ('type',      c_uint),
      ('timestamp', c_uint),
      ('windowID',  c_uint),
      ('state',     c_ubyte),
      ('repeat',    c_ubyte),
      ('padding',   c_ubyte * 2),
      ('keysym',    SDL_Keysym)]

class SDL_MouseMotionEvent(Structure):
   _fields_ = [
      ('type',      c_uint),
      ('timestamp', c_uint),
      ('windowID',  c_uint),
      ('which',     c_uint),
      ('state',     c_uint),
      ('x',         c_int),
      ('y',         c_int),
      ('xrel',      c_int),
      ('yrel',      c_int)]

class SDL_MouseButtonEvent(Structure):
   _fields_ = [
      ('type',      c_uint),
      ('timestamp', c_uint),
      ('windowID',  c_uint),
      ('which',     c_uint),
      ('button',    c_ubyte),
      ('state',     c_ubyte),
      ('clicks',    c_ubyte),
      ('padding1',  c_ubyte),
      ('x',         c_int),
      ('y',         c_int)]

class SDL_MouseWheelEvent(Structure):
   _fields_ = [
      ('type',      c_uint),
      ('timestamp', c_uint),
      ('windowID',  c_uint),
      ('which',     c_uint),
      ('x',         c_int),
      ('y',         c_int)]

class SDL_Event(Union):
   _fields_ = [
      ('type',    c_uint),
      ('window',  SDL_WindowEvent),
      ('key',     SDL_KeyboardEvent),
      ('motion',  SDL_MouseMotionEvent),
      ('button',  SDL_MouseButtonEvent),
      ('wheel',   SDL_MouseWheelEvent),
      ('padding', c_ubyte * 56)]

_load('SDL2', 'SDL_CreateRGBSurface', POINTER(SDL_Surface), [c_uint, c_int, c_int, c_int, c_uint, c_uint, c_uint, c_uint])
_load('SDL2', 'SDL_CreateWindow',     c_void_p, [c_char_p, c_int, c_int, c_int, c_int, c_uint])
_load('SDL2', 'SDL_GL_CreateContext', c_void_p, [c_void_p])
_load('SDL2', 'SDL_GL_DeleteContext', None,     [c_void_p])
_load('SDL2', 'SDL_GL_SwapWindow',    None,     [c_void_p])
_load('SDL2', 'SDL_DestroyWindow',    None,     [c_void_p])
_load('SDL2', 'SDL_FreeSurface',      None,     [POINTER(SDL_Surface)])
_load('SDL2', 'SDL_Init',             c_int,    [c_uint])
_load('SDL2', 'SDL_PollEvent',        c_int,    [POINTER(SDL_Event)])
_load('SDL2', 'SDL_Quit',             None,     [])
_load('SDL2', 'SDL_RaiseWindow',      None,     [c_void_p])
_load('SDL2', 'SDL_SetWindowIcon',    None,     [c_void_p, POINTER(SDL_Surface)])
_load('SDL2', 'SDL_UpperBlit',        c_int,    [POINTER(SDL_Surface), POINTER(SDL_Rect), POINTER(SDL_Surface), POINTER(SDL_Rect)])
_load('SDL2', 'SDL_WaitEvent',        c_int,    [POINTER(SDL_Event)])

_load('SDL2_image', 'IMG_Init', c_int,                [c_int])
_load('SDL2_image', 'IMG_Load', POINTER(SDL_Surface), [c_char_p])
_load('SDL2_image', 'IMG_Quit', None,                 [])

SDL_BUTTON_LEFT               = 0x00000001
SDL_BUTTON_MIDDLE             = 0x00000002
SDL_BUTTON_RIGHT              = 0x00000003
SDL_BUTTON_LMASK              = 0x00000001
SDL_BUTTON_MMASK              = 0x00000002
SDL_BUTTON_RMASK              = 0x00000004
SDL_INIT_EVENTS               = 0x00004000
SDL_INIT_VIDEO                = 0x00000020
SDL_KEYDOWN                   = 0x00000300
SDL_KEYUP                     = 0x00000301
SDL_MOUSEBUTTONDOWN           = 0x00000401
SDL_MOUSEBUTTONUP             = 0x00000402
SDL_MOUSEMOTION               = 0x00000400
SDL_MOUSEWHEEL                = 0x00000403
SDL_QUIT                      = 0x00000100
SDL_WINDOW_FULLSCREEN_DESKTOP = 0x00001001
SDL_WINDOW_OPENGL             = 0x00000002
SDL_WINDOW_RESIZABLE          = 0x00000020
SDL_WINDOWEVENT               = 0x00000200
SDL_WINDOWEVENT_RESIZED       = 0x00000005
SDL_WINDOWEVENT_SIZE_CHANGED  = 0x00000006
SDL_WINDOWPOS_UNDEFINED       = 0x1FFF0000

SDLK_BACKSPACE = 0x00000008
SDLK_DELETE    = 0x0000007F
SDLK_DOWN      = 0x40000051
SDLK_END       = 0x4000004D
SDLK_ESCAPE    = 0x0000001B
SDLK_F1        = 0x4000003A
SDLK_F2        = 0x4000003B
SDLK_HOME      = 0x4000004A
SDLK_INSERT    = 0x40000049
SDLK_LEFT      = 0x40000050
SDLK_PAGEDOWN  = 0x4000004E
SDLK_PAGEUP    = 0x4000004B
SDLK_RETURN    = 0x0000000D
SDLK_RIGHT     = 0x4000004F
SDLK_TAB       = 0x00000009
SDLK_UP        = 0x40000052

KMOD_ALT   = 0x0300
KMOD_CAPS  = 0x2000
KMOD_CTRL  = 0x00C0
KMOD_SHIFT = 0x0003

IMG_INIT_JPG = 0x00000001
IMG_INIT_PNG = 0x00000002
IMG_INIT_TIF = 0x00000004

#===============================================================================
# OpenGL bindings.
#===============================================================================

_load('GL', 'glBegin',          None, [c_int])
_load('GL', 'glBindTexture',    None, [c_int, c_uint])
_load('GL', 'glBlendFunc',      None, [c_int, c_int])
_load('GL', 'glClear',          None, [c_uint])
_load('GL', 'glClearColor',     None, [c_float, c_float, c_float, c_float])
_load('GL', 'glColor4d',        None, [c_double, c_double, c_double, c_double])
_load('GL', 'glDeleteTextures', None, [c_int, POINTER(c_uint)])
_load('GL', 'glDisable',        None, [c_int])
_load('GL', 'glEnable',         None, [c_int])
_load('GL', 'glEnd',            None, [])
_load('GL', 'glGenTextures',    None, [c_int, POINTER(c_uint)])
_load('GL', 'glLoadIdentity',   None, [])
_load('GL', 'glMatrixMode',     None, [c_int])
_load('GL', 'glOrtho',          None, [c_double, c_double, c_double, c_double, c_double, c_double])
_load('GL', 'glTexCoord2d',     None, [c_double, c_double])
_load('GL', 'glTexEnvi',        None, [c_int, c_int, c_int])
_load('GL', 'glTexImage2D',     None, [c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_void_p])
_load('GL', 'glTexParameteri',  None, [c_int, c_int, c_int])
_load('GL', 'glVertex2d',       None, [c_double, c_double])
_load('GL', 'glViewport',       None, [c_int, c_int, c_int, c_int])

GL_BLEND               = 0x0BE2
GL_COLOR_BUFFER_BIT    = 0x4000
GL_LINE_LOOP           = 0x0002
GL_LINES               = 0x0001
GL_LINEAR              = 0x2601
GL_MODELVIEW           = 0x1700
GL_MODULATE            = 0x2100
GL_NEAREST             = 0x2600
GL_ONE                 = 0x0001 
GL_ONE_MINUS_SRC_ALPHA = 0x0303
GL_PROJECTION          = 0x1701
GL_QUADS               = 0x0007
GL_REPEAT              = 0x2901
GL_REPLACE             = 0x1E01
GL_RGBA                = 0x1908
GL_RGBA8               = 0x8058
GL_SRC_ALPHA           = 0x0302
GL_TEXTURE_2D          = 0x0DE1
GL_TEXTURE_ENV         = 0x2300
GL_TEXTURE_ENV_MODE    = 0x2200
GL_TEXTURE_MAG_FILTER  = 0x2800
GL_TEXTURE_MIN_FILTER  = 0x2801
GL_TEXTURE_WRAP_S      = 0x2802
GL_TEXTURE_WRAP_T      = 0x2803
GL_TRIANGLES           = 0x0004
GL_UNSIGNED_BYTE       = 0x1401
GL_ZERO                = 0x0000
