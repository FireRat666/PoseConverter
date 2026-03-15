# ==============================================================================
#  FireRat ‑ Pose Converter
#  __init__.py  ―  Addon entry point
# ==============================================================================

bl_info = {
    "name": "Pose Converter",
    "author": "FireRat",
    "version": (0, 1, 2),
    "blender": (3, 6, 0),
    "location": "View3D > Tool Shelf > FireRat",
    "description": "Copy pose from one armature to another and apply it as a rest pose.",
    "category": "Rigging",
}

import bpy

# -----------------------------------------------------------------------------
#  Internal Module Imports
# -----------------------------------------------------------------------------
from .ui_panel import PoseToolPanel, PoseConverterProperties
from .ops_convert_pose import (
    POSECONV_OT_ConvertPose,
    POSECONV_OT_SetRestPose,
)
# bone_finder is no longer used for the core logic.
# from .bone_finder import POSECONV_OT_DetectBones

# -----------------------------------------------------------------------------
#  Addon Registration / Unregistration
# -----------------------------------------------------------------------------
_classes = (
    PoseConverterProperties,
    PoseToolPanel,
    POSECONV_OT_ConvertPose,
    POSECONV_OT_SetRestPose,
    # POSECONV_OT_DetectBones, # No longer needed
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    # Add tool properties to the Scene
    bpy.types.Scene.pose_converter_props = bpy.props.PointerProperty(
        type=PoseConverterProperties
    )


def unregister():
    # Remove Scene properties
    del bpy.types.Scene.pose_converter_props

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
