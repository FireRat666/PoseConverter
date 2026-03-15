import bpy
from bpy.types import Operator
import traceback
import os
from .utils import (
    write_log,
    find_related_mesh_objects,
    apply_new_armature_modifier
)

def apply_as_rest_pose(armature_obj):
    """Applies the current pose as the rest pose."""
    original_mode = bpy.context.mode
    
    bpy.context.view_layer.objects.active = armature_obj
    
    if original_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Switch to Pose Mode
    bpy.ops.object.mode_set(mode='POSE')
    
    # IMPORTANT: Select all bones to ensure the apply affects everything
    bpy.ops.pose.select_all(action='SELECT')
    
    # Apply Pose as Rest Pose
    bpy.ops.pose.armature_apply()
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    if original_mode == 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    
    write_log("Applied current pose as rest pose")

def strip_prefix(name):
    """Strips common prefixes from bone names for better matching."""
    if ":" in name:
        return name.split(":")[-1]
    return name

def copy_pose_from_target(source_arm, target_arm):
    """
    Copies the pose from the target armature to the source armature using CONSTRAINTS.
    This ensures visual matching regardless of Rest Pose differences.
    """
    try:
        write_log("--- Starting Pose Copy (Constraint Method) ---")
        write_log(f"Source Armature: {source_arm.name}")
        write_log(f"Target Armature: {target_arm.name}")
        
        # Ensure we are in Pose Mode
        bpy.context.view_layer.objects.active = source_arm
        bpy.ops.object.mode_set(mode='POSE')
        
        # Deselect all to start clean
        bpy.ops.pose.select_all(action='DESELECT')
        
        # Build a map of normalized bone names for the target armature
        target_bones_map = {strip_prefix(b.name): b for b in target_arm.pose.bones}
        
        constraints_to_remove = []
        matched_count = 0
        
        for source_bone in source_arm.pose.bones:
            normalized_name = strip_prefix(source_bone.name)
            target_bone = target_bones_map.get(normalized_name)
            
            if target_bone:
                # Select the bone so visual_transform_apply works on it
                source_bone.bone.select = True
                matched_count += 1
                
                # Add Copy Rotation Constraint
                c_rot = source_bone.constraints.new('COPY_ROTATION')
                c_rot.target = target_arm
                c_rot.subtarget = target_bone.name
                c_rot.name = "TEMP_POSE_CONV_ROT"
                # Defaults are World <-> World, which is what we want
                
                constraints_to_remove.append((source_bone, c_rot))
                
                # If root bone (no parent), copy Location too
                if source_bone.parent is None:
                    c_loc = source_bone.constraints.new('COPY_LOCATION')
                    c_loc.target = target_arm
                    c_loc.subtarget = target_bone.name
                    c_loc.name = "TEMP_POSE_CONV_LOC"
                    constraints_to_remove.append((source_bone, c_loc))
        
        if matched_count == 0:
            write_log("CRITICAL: No matching bones found! Check bone names.")
            return False
            
        write_log(f"Added constraints to {matched_count} bones. Applying visual transform...")
        
        # Update dependency graph
        bpy.context.view_layer.update()
        
        # Bake the constraints into the Pose
        # This calculates the Loc/Rot/Scale needed to match the constraints visually
        bpy.ops.pose.visual_transform_apply()
        
        # Remove constraints
        for bone, constraint in constraints_to_remove:
            bone.constraints.remove(constraint)
            
        write_log("Constraints removed. Pose copy complete.")
        return True
        
    except Exception as e:
        write_log(f"--- CRITICAL ERROR in copy_pose_from_target ---")
        write_log(f"Error: {e}")
        write_log(traceback.format_exc())
        return False

def import_armature_from_blend(filepath):
    """
    Appends an armature from a .blend file into the current scene.
    Returns the appended object or None.
    """
    try:
        write_log(f"Appending armature from: {filepath}")
        
        # Load all objects from the blend file
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            # We want to import objects, specifically armatures
            # We assume the file contains at least one object that is an armature
            data_to.objects = [name for name in data_from.objects]
            
        imported_objects = []
        target_armature = None
        
        # Link objects to scene and find the armature
        for obj in data_to.objects:
            if obj:
                bpy.context.collection.objects.link(obj)
                imported_objects.append(obj)
                if obj.type == 'ARMATURE' and target_armature is None:
                    target_armature = obj
        
        if target_armature:
            write_log(f"Successfully imported armature: {target_armature.name}")
            return target_armature, imported_objects
        else:
            write_log("No armature found in the specified .blend file.")
            # Cleanup if no armature found
            for obj in imported_objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            return None, []
            
    except Exception as e:
        write_log(f"Error importing from .blend: {e}")
        return None, []

def save_mesh_as_shape_key(arm_obj, mesh_obj, report_fn):
    """Saves the current deformation of the mesh as a shape key."""
    try:
        write_log(f"Saving mesh '{mesh_obj.name}' as shape key...")
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        
        arm_modifier = next((mod for mod in mesh_obj.modifiers if mod.type == 'ARMATURE' and mod.object == arm_obj), None)
        
        if not arm_modifier:
            arm_modifier = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
            arm_modifier.object = arm_obj
            write_log(f"Created new armature modifier for mesh '{mesh_obj.name}'")
        
        bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=True, modifier=arm_modifier.name)
        write_log(f"Saved current deformation as shape key for mesh '{mesh_obj.name}'")
        
        if mesh_obj.data.shape_keys and mesh_obj.data.shape_keys.key_blocks:
            new_shape_key = mesh_obj.data.shape_keys.key_blocks[-1]
            new_shape_key.name = "PoseConverterBackup"
            write_log(f"Renamed shape key to 'PoseConverterBackup' for mesh '{mesh_obj.name}'")
            return True
        else:
            report_fn({'WARNING'}, f"Failed to create shape key for mesh '{mesh_obj.name}'")
            return False
            
    except Exception as e:
        write_log(f"Error saving mesh as shape key for '{mesh_obj.name}': {e}")
        report_fn({'ERROR'}, f"Failed to save mesh as shape key: {e}")
        return False

def process_shape_keys_after_rest_pose(mesh_obj, report_fn):
    """Processes shape keys after applying the rest pose."""
    try:
        write_log(f"Processing shape keys for mesh '{mesh_obj.name}'...")
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        
        if not mesh_obj.data.shape_keys:
            return False
        
        base_change_key = mesh_obj.data.shape_keys.key_blocks.get('PoseConverterBackup')
        if not base_change_key:
            return False
        
        basis_key = mesh_obj.data.shape_keys.key_blocks[0]
        basis_key_name = basis_key.name
        
        base_change_key.value = 1.0
        
        shape_keys_list = [key for key in mesh_obj.data.shape_keys.key_blocks if key != base_change_key and key != basis_key]
        
        for shape_key in list(shape_keys_list):
            original_name = shape_key.name
            original_value = shape_key.value
            
            shape_key.value = 1.0
            mesh_obj.shape_key_add(name="PoseConverterTemp", from_mix=True)
            temp_key = mesh_obj.data.shape_keys.key_blocks["PoseConverterTemp"]
            
            idx = mesh_obj.data.shape_keys.key_blocks.find(original_name)
            if idx != -1:
                mesh_obj.active_shape_key_index = idx
                bpy.ops.object.shape_key_remove()
            
            temp_key.name = original_name
            temp_key.value = original_value
        
        for k in mesh_obj.data.shape_keys.key_blocks:
            k.value = 0.0
        
        base_change_key.value = 1.0
        catbasis_idx = mesh_obj.data.shape_keys.key_blocks.find('PoseConverterBackup')
        mesh_obj.active_shape_key_index = catbasis_idx
        bpy.ops.object.shape_key_move(type='TOP')
        
        basis_idx = mesh_obj.data.shape_keys.key_blocks.find(basis_key_name)
        if basis_idx != -1:
            mesh_obj.active_shape_key_index = basis_idx
            bpy.ops.object.shape_key_remove()
        
        mesh_obj.data.shape_keys.key_blocks[0].name = basis_key_name
        write_log(f"Set '{basis_key_name}' as new basis for mesh '{mesh_obj.name}'")
        
        return True
        
    except Exception as e:
        write_log(f"Error processing shape keys for '{mesh_obj.name}': {e}")
        report_fn({'ERROR'}, f"Shape key processing failed: {e}")
        return False

def process_without_shape_keys(arm_obj, mesh_obj, report_fn):
    """Processes meshes without shape keys."""
    try:
        write_log(f"Processing mesh '{mesh_obj.name}' without shape keys...")
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        arm_obj.select_set(False)
        
        if mesh_obj.data.users > 1:
            mesh_obj.data = mesh_obj.data.copy()
        
        if not apply_new_armature_modifier(mesh_obj, arm_obj, report_fn):
            report_fn({'ERROR'}, f"Failed to apply armature modifier to mesh '{mesh_obj.name}'")
            return False
        
        return True
        
    except Exception as e:
        write_log(f"Error processing mesh '{mesh_obj.name}' without shape keys: {e}")
        report_fn({'ERROR'}, f"Process failed for mesh '{mesh_obj.name}': {e}")
        return False

class POSECONV_OT_ConvertPose(Operator):
    bl_idname = "poseconv.convert_pose"
    bl_label = "Match Pose and Apply as Rest"
    bl_description = "Copy pose from target and apply as the new rest pose, preserving shape keys"
    bl_options = {'REGISTER', 'UNDO'} 

    def execute(self, context):
        write_log("Starting pose conversion...")
        
        arm_obj = context.object
        props = context.scene.pose_converter_props
        
        if not arm_obj or arm_obj.type != 'ARMATURE':
            self.report({'WARNING'}, "Select a source Armature object.")
            return {'CANCELLED'}
        
        # 1. Acquire Target Armature
        target_arm = None
        imported_objects = []
        
        if props.target_source == 'CUSTOM':
            target_arm = props.target_armature
            if not target_arm:
                self.report({'WARNING'}, "Select a target Armature.")
                return {'CANCELLED'}
        else:
            # Import default pose from .blend file
            filename = "male_default.blend" if props.target_source == 'MALE' else "female_default.blend"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            if not os.path.exists(filepath):
                 self.report({'ERROR'}, f"Pose data file not found: {filename}")
                 return {'CANCELLED'}
            
            target_arm, imported_objects = import_armature_from_blend(filepath)
            if not target_arm:
                self.report({'ERROR'}, "Failed to import armature from file.")
                return {'CANCELLED'}

        # 2. Copy the pose
        try:
            if not copy_pose_from_target(arm_obj, target_arm):
                self.report({'ERROR'}, "Pose copying failed or no bones matched.")
                # Cleanup imported objects if failed
                if imported_objects:
                    for obj in imported_objects:
                        bpy.data.objects.remove(obj, do_unlink=True)
                return {'CANCELLED'}
        except Exception as e:
             # Cleanup on error
             if imported_objects:
                 for obj in imported_objects:
                     bpy.data.objects.remove(obj, do_unlink=True)
             raise e

        # Cleanup imported objects now that pose is copied (Constraints are baked and removed inside copy_pose_from_target)
        if imported_objects:
            write_log("Removing imported temporary armature...")
            for obj in imported_objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        try:
            # 3. Process Meshes
            related_meshes = find_related_mesh_objects(arm_obj)
            if not related_meshes:
                self.report({'WARNING'}, "No meshes found for the selected armature. Pose copied but not applied to meshes.")
                return {'FINISHED'}

            meshes_with_shape_keys = [m for m in related_meshes if m.data.shape_keys]
            meshes_without_shape_keys = [m for m in related_meshes if not m.data.shape_keys]
            
            for mesh_obj in meshes_with_shape_keys:
                save_mesh_as_shape_key(arm_obj, mesh_obj, self.report)
            
            for mesh_obj in meshes_without_shape_keys:
                process_without_shape_keys(arm_obj, mesh_obj, self.report)
            
            # 4. Apply as Rest Pose
            bpy.context.view_layer.objects.active = arm_obj
            arm_obj.select_set(True)
            for mesh_obj in related_meshes:
                mesh_obj.select_set(False)
            
            apply_as_rest_pose(arm_obj)
            
            # 5. Cleanup Shape Keys
            for mesh_obj in meshes_with_shape_keys:
                process_shape_keys_after_rest_pose(mesh_obj, self.report)
            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.update()
            
            self.report({'INFO'}, f"Pose matched and applied as rest pose successfully.")

        except Exception as e:
            self.report({'ERROR'}, f"Pose conversion failed: {e}")
            write_log(traceback.format_exc())
            return {'CANCELLED'}

        return {'FINISHED'}
    
class POSECONV_OT_SetRestPose(Operator):
    bl_idname = "poseconv.set_rest_pose"
    bl_label = "Set Current as Rest Pose"
    bl_description = "Set current pose as rest pose and update meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = context.object
        
        if not arm_obj or arm_obj.type != 'ARMATURE':
            self.report({'WARNING'}, "Select a valid Armature object.")
            return {'CANCELLED'}

        related_meshes = find_related_mesh_objects(arm_obj)
        if not related_meshes:
            self.report({'WARNING'}, "No meshes found for the selected armature.")
            return {'CANCELLED'}

        try:
            meshes_with_shape_keys = [m for m in related_meshes if m.data.shape_keys]
            meshes_without_shape_keys = [m for m in related_meshes if not m.data.shape_keys]
            
            for mesh_obj in meshes_with_shape_keys:
                save_mesh_as_shape_key(arm_obj, mesh_obj, self.report)
            
            for mesh_obj in meshes_without_shape_keys:
                process_without_shape_keys(arm_obj, mesh_obj, self.report)
            
            bpy.context.view_layer.objects.active = arm_obj
            arm_obj.select_set(True)
            for mesh_obj in related_meshes:
                mesh_obj.select_set(False)
            
            apply_as_rest_pose(arm_obj)
            
            for mesh_obj in meshes_with_shape_keys:
                process_shape_keys_after_rest_pose(mesh_obj, self.report)
            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.update()
            
            self.report({'INFO'}, f"Rest pose set successfully.")

        except Exception as e:
            self.report({'ERROR'}, f"Set rest pose failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

def register():
    bpy.utils.register_class(POSECONV_OT_ConvertPose)
    bpy.utils.register_class(POSECONV_OT_SetRestPose)

def unregister():
    bpy.utils.unregister_class(POSECONV_OT_SetRestPose)
    bpy.utils.unregister_class(POSECONV_OT_ConvertPose)
