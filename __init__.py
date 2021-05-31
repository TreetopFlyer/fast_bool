import bpy
import random

class FBBase(bpy.types.Operator):
    """Initialize object as base (with mirror, remesh, etc)"""
    bl_idname = "fb.base"
    bl_label = "Fast Bool: Base"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mod = context.active_object.modifiers.new(type="MIRROR", name="FB.Mirror")
        mod.use_bisect_axis[0] = True
        mod.use_clip = True
        
        smoothBevel(context.active_object.modifiers)
        return {'FINISHED'}
  

def smoothBevel(modifiers) :
    mod = modifiers.new(type="BEVEL", name="FB.Display.Mesh")
    mod.limit_method = "ANGLE"
    mod.segments = 3
    modifiers.new(type="WEIGHTED_NORMAL", name="FB.Display.Smooth")

def smoothVoxel(modifiers) :
    mod = modifiers.new(type="REMESH", name="FB.Display.Mesh")
    mod.octree_depth = 7
    mod.mode = "SMOOTH"
    mod.use_remove_disconnected = False
    mod = modifiers.new(type="SMOOTH", name="FB.Display.Smooth")
    mod.factor = 1
    mod.iterations = 5

class FBSmoothing(bpy.types.Operator):
    """set smoothing type for object"""
    bl_idname = "fb.smoothing"
    bl_label = "Fast Bool: Smoothing"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mods = context.active_object.modifiers;
        isVox = False
        for m in mods :
            if m.name.startswith("FB.Display") :
                if m.type == "REMESH":
                    isVox = True
                mods.remove(m)
                
        if isVox :
            smoothBevel(mods)
        else :
            smoothVoxel(mods)
                
        return {'FINISHED'}

class FBApply(bpy.types.Operator):
    """Add selected objects as booleans to active object"""
    bl_idname = "fb.apply"
    bl_label = "Fast Bool: Apply"
    bl_options = {'REGISTER', 'UNDO'}


    mode = bpy.props.IntProperty(name="Mode", default=0)

    def execute(self, context):
        
        modes = [
            {"Name":"Add", "Op":"UNION"},
            {"Name":"Subract", "Op":"DIFFERENCE"},
            {"Name":"Intersect", "Op":"INTERSECT"},
            {"Name":"Split", "Op":"DIFFERENCE"}
        ]
        
        selected = context.selected_objects
        active = context.active_object
        height = len(active.modifiers)
        mode = modes[self.mode]
        rand = str(random.randint(10000, 20000))
        
        for other in selected:
            if other != active:
                modName = "FB."+mode["Name"]+"."+other.name+"."+rand
                other.display_type = "BOUNDS"
                other.hide_render = True
                mod = active.modifiers.new(type = "BOOLEAN", name = modName)
                mod.object = other
                mod.operation = mode["Op"]
                for i in range(height) :
                    bpy.ops.object.modifier_move_up(modifier=modName)
                    
                if mode["Name"] == "Split" :
                    mod = other.modifiers.new(type="SOLIDIFY", name="FB.Shell")
                    mod.thickness = 0.25
        
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)
        
        print(mode)
        
        for m in context.selected_objects[0].modifiers:
            print(m)
        return {'FINISHED'}

class FBRemove(bpy.types.Operator):
    """Remove selected objects used in FastBool Apply"""
    bl_idname = "fb.remove"
    bl_label = "Fast Bool: Remove"
    bl_options = {'REGISTER', 'UNDO'}
 
    def execute(self, context):
        
        selected = context.selected_objects
        
        for other in selected:
            other.display_type = "TEXTURED"
            other.hide_render = False
            
            for omod in other.modifiers :
                if omod.type == "SOLIDIFY" and omod.name.startswith("FB.") :
                    print("removing shell modifier "+omod.name)
                    other.modifiers.remove(omod)
                    
            if other.parent != None :
                for pmod in other.parent.modifiers :
                    if pmod.type == "BOOLEAN" and pmod.object == other :
                        print("removing boolean: "+pmod.name)
                        other.parent.modifiers.remove(pmod)

        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        return {'FINISHED'};
 
 
class FBCommit(bpy.types.Operator):
    """Commit all booleans"""
    bl_idname = "fb.commit"
    bl_label = "Fast Bool: Commit"
    bl_options = {'REGISTER', 'UNDO'}
 
    def execute(self, context):
        
        selected = context.selected_objects
        
        for object in selected:
            for mod in object.modifiers :
                if mod.type == "BOOLEAN" and mod.name.startswith("FB.") :
                    print("committing boolean modifier "+mod.name)
                    bpy.ops.object.modifier_apply(modifier=mod.name)

                    
        return {'FINISHED'};
 

class FBToggle(bpy.types.Operator):
    """toggle visibility of children"""
    bl_idname = "fb.toggle"
    bl_label = "Fast Bool: Toggle Children Display"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        selected = context.selected_objects
        
        for object in selected:
            for child in object.children :
                child.hide_viewport = not child.hide_viewport

        return {'FINISHED'};
        

class FBPie(bpy.types.Menu):
    bl_label = "Fast Bool"
    
    def draw(self, context):
        
        pie = self.layout.menu_pie()
        
        box = pie.split().box()
        op = box.operator("fb.base", text="Initialize")
        op = box.operator("fb.smoothing", text="Switch Smoothing")
        op = box.operator("fb.toggle", text="Toggle Chidren")
        op = box.operator("fb.commit", text="Bake Booleans")
        
        box = pie.split().box()
        op = box.operator("fb.apply", text="Add")
        op.mode = 0
        op = box.operator("fb.apply", text="Subtract")
        op.mode = 1
        op = box.operator("fb.apply", text="Intersect")
        op.mode = 2
        op = box.operator("fb.apply", text="Split")
        op.mode = 3
        
        op = pie.operator("fb.remove", text="Remove")




FBClasses = [FBBase, FBApply, FBRemove, FBCommit, FBPie, FBToggle, FBSmoothing]

def register():
    for FBClass in FBClasses :
        bpy.utils.register_class(FBClass)

def unregister():
    for FBClass in FBClasses :
        bpy.utils.unregister_class(FBClass)


if __name__ == "__main__":
    register()  
    
# console test:
# bpy.ops.fb.base("INVOKE_DEFAULT")
# bpy.ops.fb.apply("INVOKE_DEFAULT", mode=3)
# bpy.ops.fb.remove("INVOKE_DEFAULT")

# keybind this:
# bpy.ops.wm.call_menu_pie("FBPie")