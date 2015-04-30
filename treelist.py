# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Tree List",
    "description": " List of node trees to switch between quickly",
    "author": "Greg Zaal",
    "version": (0, 1),
    "blender": (2, 73, 0),
    "location": "Node Editor > Tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Node"}

import bpy


'''
TODOs:
    Show lights
    Make options panel with:
        Show materials with no users
        Show world settings of all scenes
        Show only materials for objects in current scene
    Assign material to selected objects
    Recenter all trees
    Material Templates
        Set of decent starting points, like diffuse + glossy with fresnel
        Let user add own templates (from node groups?)
'''

def get_materials():
    materials = []
    for mat in bpy.data.materials:
        conditions = [
            mat.users,  # TODO make this optional
            not mat.library,  # don't allow editing of linked library materials - TODO make this optional (can help to be able to look at the nodes, even if you can't edit it)
            mat.use_nodes]
        if all(conditions):
            materials.append(mat)

    return materials

def dummy_object(delete=False):
    ''' Return the existing dummy object, or create one if it doesn't exist. '''
    scene = bpy.context.scene

    if delete:
        for obj in scene.objects:
            if "TreeList Dummy Object" in obj.name:
                scene.objects.unlink(obj)
        return "DONE"
    
    dummy = None
    previous_dummy = [obj for obj in bpy.data.objects if obj.name == "TreeList Dummy Object"]
    if previous_dummy:
        dummy = previous_dummy[0]
    else:
        m = bpy.data.meshes.new("TreeList Dummy Mesh")
        dummy = bpy.data.objects.new("TreeList Dummy Object", m)

    if dummy not in list(obj for obj in scene.objects):
        scene.objects.link(dummy)

    dummy.select = True
    scene.objects.active = dummy

    if len(dummy.material_slots) == 0:
        bpy.ops.object.material_slot_add()
        
    return dummy


class TreeListSettings(bpy.types.PropertyGroup):
    expand_materials = bpy.props.BoolProperty(
        name="Expand Materials",
        default=True,
        description="Show the list of materials")

    expand_lighting = bpy.props.BoolProperty(
        name="Expand Lighting",
        default=True,
        description="Show the list of lights")


class TLGoTo(bpy.types.Operator):

    'Show the nodes for this material'
    bl_idname = 'treelist.goto'
    bl_label = 'Go To'
    mat = bpy.props.StringProperty(default = "")
    world = bpy.props.BoolProperty(default = False)

    def execute(self, context):
        dummy_object(delete=True)
        scene = context.scene
        context.space_data.tree_type = 'ShaderNodeTree'
        if self.world:
            context.space_data.shader_type = 'WORLD'
        else:
            context.space_data.shader_type = 'OBJECT'
            mat = bpy.data.materials[self.mat]

            objs_with_mat = 0
            active_set = False
            for obj in scene.objects:
                obj_materials = [slot.material for slot in obj.material_slots]
                if mat in obj_materials:
                    objs_with_mat += 1
                    obj.select = True
                    if not active_set:  # set first object as active
                        active_set = True
                        scene.objects.active = obj
                        if mat != obj.active_material:
                            for i, x in enumerate(obj.material_slots):
                                if x.material == mat:
                                    obj.active_material_index = i
                                    break
                else:
                    obj.select = False

            if objs_with_mat == 0:
                self.report({'WARNING'}, "No objects in this scene use '" + mat.name + "' material")
                dummy = dummy_object()
                slot = dummy.material_slots[0]
                slot.material = mat

        return {'FINISHED'}


class TreeListMaterials(bpy.types.Panel):

    bl_label = "Materials"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_category = "Trees"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'CYCLES'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        materials = get_materials()
        settings = scene.treelist_settings

        col = layout.column(align=True)

        for mat in materials:
            name = mat.name
            try:
                icon_val = layout.icon(mat)
            except:
                icon_val = 1
                print ("WARNING [Mat Panel]: Could not get icon value for %s" % name)
            op = col.operator('treelist.goto', text=name, emboss=(mat==context.space_data.id), icon_value=icon_val)
            op.mat = name
            op.world = False


class TreeListLighting(bpy.types.Panel):

    bl_label = "Lighting"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_category = "Trees"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'CYCLES'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        materials = bpy.data.materials
        settings = scene.treelist_settings

        col = layout.column(align=True)

        if context.scene.world.use_nodes:
            op = col.operator('treelist.goto', text="World", emboss=(context.scene.world==context.space_data.id), icon='WORLD')
            op.world = True


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.treelist_settings = bpy.props.PointerProperty(type=TreeListSettings)

def unregister():
    del bpy.types.Scene.treelist_settings

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
