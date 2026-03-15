import bpy
from bpy.props import PointerProperty, EnumProperty
from bpy.types import Panel, PropertyGroup
from .utils import find_related_mesh_objects

class PoseConverterProperties(PropertyGroup):
    target_source: EnumProperty(
        name="Target Source",
        description="Choose the source for the target pose",
        items=[
            ('CUSTOM', "Custom", "Use a custom armature from the scene"),
            ('MALE', "Default Male", "Use the default male A-pose"),
            ('FEMALE', "Default Female", "Use the default female A-pose")
        ],
        default='CUSTOM'
    )
    
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
        armature = context.object if context.object and context.object.type == 'ARMATURE' else None
        
        main_box = layout.box()
        main_box.label(text="Main Conversion", icon='POSE_HLT')
        
        row = main_box.row()
        row.label(text="Source Armature:")
        if armature:
            row.label(text=armature.name, icon='ARMATURE_DATA')
        else:
            row.label(text="Select Source Armature", icon='ERROR')
        
        main_box.separator()
        
        # Target Source Selection
        main_box.prop(props, "target_source")
        
        # Conditional UI for target armature
        if props.target_source == 'CUSTOM':
            main_box.prop(props, "target_armature")
            target = props.target_armature
            if target and target == armature:
                main_box.label(text="Source and Target cannot be the same", icon='ERROR')
        
        main_box.separator()

        # Determine if the operator should be enabled
        is_ready = False
        if armature:
            if props.target_source != 'CUSTOM':
                is_ready = True
            elif props.target_armature and props.target_armature != armature:
                is_ready = True

        # Action Buttons
        col = main_box.column(align=True)
        col.enabled = is_ready
        col.scale_y = 1.5
        col.operator("poseconv.convert_pose", text="Match Pose & Apply Rest", icon='POSE_HLT')
        
        layout.separator()
        
        # Utilities Box
        utils_box = layout.box()
        utils_box.label(text="Utilities", icon='TOOL_SETTINGS')
        
        # Rest Pose Button
        rest_row = utils_box.row()
        rest_row.enabled = bool(armature)
        rest_row.operator("poseconv.set_rest_pose", text="Apply Current Pose as Rest", icon='ARMATURE_DATA')


def register():
    bpy.utils.register_class(PoseConverterProperties)
    bpy.utils.register_class(PoseToolPanel)

def unregister():
    bpy.utils.unregister_class(PoseToolPanel)
    bpy.utils.unregister_class(PoseConverterProperties)
