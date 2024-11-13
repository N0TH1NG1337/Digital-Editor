# User Interface. Scene .py

import OpenGL.GL as gl
import glfw
import imgui

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.math     import  math
from utilities.safe     import  safe_call
from utilities.image    import  c_image
from utilities.font     import  c_font
from utilities.event    import  c_event

from user_interface.render      import c_renderer
from user_interface.animation   import c_animations

# This is preatty similar to scene, however scene is a must object while window can be optional
# Moreover, scene is on full size application, while window is a sub scene with custom position and size.

# Note ! Since we are going to attach widgets to c_window also, we must copy all the same functions like c_scene
# In addition, we will have to update the position of each element each frame.

# WARNING ! Update each widget will be problematic, since we have the _position in each widget that is relative to top corner.
# we will need to handle manually the position change of window and add the delta movement for each widget and by that moving widgets
# with the window

# Interaction handle !
# While we could use the active handle, this will be cancer, since the index will be len(ui) + self._index
# What we can do, is the get the last window in the list, and force interaction handle on it. 
# If the list is empty, enable interaction for everything else

class c_window:

    _parent:        any     # c_scene
    _index:         int

    _position:      vector
    _size:          vector

    _show:          bool
    _events:        dict
    _ui:            list

    _render:        c_renderer
    _animations:    c_animations

    _config:        dict

    _active_handle: int
    
    def __init__(self):
        pass


    def index( self, new_value: int = None ) -> int:
        """
            Returns / Sets the current scene index in the queue
        """
        if new_value is None:
            return self._index
        
        self._index = new_value