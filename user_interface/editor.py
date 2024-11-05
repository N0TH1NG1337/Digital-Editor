# User Interface. Widget -> Editor .py

import glfw
import os

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.math     import  math
from utilities.safe     import  safe_call
from utilities.image    import  c_image
from utilities.font     import  c_font
from utilities.event    import  c_event

from user_interface.render      import c_renderer
from user_interface.animation   import c_animations
from user_interface.scene       import c_scene


class c_editor:
    # This is our text editor. Main idea of the project.
    # In any way, we are going to work on this most of the time, fixing bugs,
    # including new features and more. 

    # What it might lack ? 
    # Right click (open new options)

    # What it must have ?
    # 1. Option to select line
    # 2. Option to disable input for other lines
    # 3. Option to write multiple lines
    # 4. Select text ( will not ignore lines that cannot be edited )

    pass