import bpy
from bpy.props import PointerProperty
from bpy.types import Panel, PropertyGroup
from .utils import find_related_mesh_objects

class PoseConverterProperties(PropertyGroup):
    target_armature: PointerProperty(
        name="Target Armature",
        description="Armature with the desired pose to copy from",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE'
    )

class PoseToolPanel(Panel):
    bl_label = "Pose Converter"
    bl_idname = "VIEW3D_PT_pose_converter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FireRat'

    def draw(self, context):
        layout = self.layout
        props = context.scene.pose_converter_props
        
        # Source Armature (Active Object)
        armature = None
        if context.object and context.object.type == 'ARMATURE':
            armature = context.object
        
        row = layout.row()
        row.label(text="Source Armature:")
        if armature:
            row.label(text=armature.name, icon='ARMATURE_DATA')
        else:
            row.label(text="Select Source Armature", icon='ERROR')
            
        # Target Armature Selection
        layout.prop(props, "target_armature")
        
        target = props.target_armature
        if target and target == armature:
             layout.label(text="Source and Target cannot be the same", icon='ERROR')

        layout.separator()

        # Related Meshes info
        if armature:
            related_meshes = find_related_mesh_objects(armature)
            
            mesh_box = layout.box()
            mesh_box.label(text=f"Related Meshes ({len(related_meshes)})", icon='OUTLINER_OB_MESH')
            
            if related_meshes:
                mesh_col = mesh_box.column(align=True)
                for mesh in related_meshes:
                    mesh_row = mesh_col.row()
                    mesh_row.label(text=mesh.name, translate=False)
                    
                    # Check for shape keys
                    has_shape_keys = mesh.data.shape_keys is not None and len(mesh.data.shape_keys.key_blocks) > 0
                    if has_shape_keys:
                        mesh_row.label(text="Has Shape Keys", icon='SHAPEKEY_DATA')
                    else:
                        mesh_row.label(text="No Shape Keys", icon='MESH_DATA')
            else:
                mesh_box.label(text="No meshes found with Armature modifier", icon='INFO')
        
        layout.separator()
        
        # Action Buttons
        col = layout.column(align=True)
        col.enabled = bool(armature and target and target != armature)
        col.scale_y = 1.5
        col.operator("poseconv.convert_pose", text="Match Pose", icon='POSE_HLT')
        
        layout.separator()
        
        # Rest Pose Button
        rest_box = layout.box()
        rest_box.label(text="Apply as Rest Pose", icon='ARMATURE_DATA')
        rest_row = rest_box.row()
        rest_row.scale_y = 1.2
        rest_row.enabled = bool(armature)
        rest_row.operator("poseconv.set_rest_pose", text="Apply Current Pose as Rest Pose", icon='ARMATURE_DATA')
        rest_box.label(text="Apply current pose to mesh and armature", icon='INFO')

def register():
    bpy.utils.register_class(PoseConverterProperties)
    bpy.utils.register_class(PoseToolPanel)

def unregister():
    bpy.utils.unregister_class(PoseToolPanel)
    bpy.utils.unregister_class(PoseConverterProperties)
