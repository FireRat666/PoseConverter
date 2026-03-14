import bpy
import datetime
import os

def get_addon_log_path():
    temp_dir = bpy.app.tempdir if bpy.app.tempdir else os.path.expanduser("~")
    log_dir = os.path.join(temp_dir, "pose_converter_logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "pose_converter_log.txt")

def write_log(message: str):
    # Print to Blender Console (Window > Toggle System Console)
    print(f"[PoseConverter] {message}")
    
    # Also write to file
    try:
        log_path = get_addon_log_path()
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")
    except Exception as e:
        print(f"[PoseConverter] Failed to write to log file: {e}")

def print_and_log(report_fn, level: str, message: str):
    report_fn({level}, message)
    write_log(f"{level.upper()}: {message}")

def get_shape_key_values(obj):
    if not obj.data.shape_keys:
        return {}
    return {kb.name: kb.value for kb in obj.data.shape_keys.key_blocks}

def restore_shape_key_values(obj, key_values):
    if not obj.data.shape_keys:
        return
    for name, value in key_values.items():
        if name in obj.data.shape_keys.key_blocks:
            obj.data.shape_keys.key_blocks[name].value = value

def find_related_mesh_objects(arm_obj):
    """
    Find mesh objects associated with an armature modifier.
    
    Parameters:
        arm_obj: Armature object
        
    Returns:
        A list of related mesh objects
    """
    related_meshes = []
    
    # Search for meshes associated with an armature modifier
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for modifier in obj.modifiers:
                if modifier.type == 'ARMATURE' and modifier.object == arm_obj:
                    if obj not in related_meshes:
                        related_meshes.append(obj)
    
    return related_meshes

def apply_shape_key_as_basis(obj, key_name):
    """
    Apply the specified shape key as the Basis and rebuild all other shape keys
    as relative deformations to the new Basis.
    """
    if not obj.data.shape_keys:
        write_log("No shape keys found")
        return
        
    kb = obj.data.shape_keys.key_blocks
    if key_name not in kb:
        raise ValueError(f"Shape key '{key_name}' not found")
    
    write_log(f"Applying shape key '{key_name}' as new Basis")
    
    # Activate the shape key that will become the new Basis
    new_basis_key = kb[key_name]
    new_basis_key.value = 1.0
    
    # Get the Basis key (usually the first key)
    basis_key = kb[0] if len(kb) > 0 else None
    
    # Create a list of shape keys to process (excluding Basis and the new Basis)
    shape_keys_to_process = [
        key for key in kb 
        if key != new_basis_key and key != basis_key and key.name != 'Basis'
    ]
    
    write_log(f"Found {len(shape_keys_to_process)} shape keys to rebuild")
    
    # Process each shape key
    for shape_key in shape_keys_to_process:
        # Save the original value
        original_name = shape_key.name
        original_value = shape_key.value
        write_log(f"Rebuilding shape key: {original_name}")
        
        # Deactivate all shape keys
        for k in kb:
            k.value = 0.0
            
        # Activate the shape key to be processed
        shape_key.value = 1.0
        
        # Create a temporary key from the current mix
        bpy.ops.object.shape_key_add(from_mix=True)
        # Get the last added shape key
        temp_key = kb[-1]
        # Change the name
        temp_key.name = "temp"
        
        # Remove the original shape key
        obj.active_shape_key_index = kb.find(original_name)
        bpy.ops.object.shape_key_remove()
        
        # Rename the temporary key to the original name
        temp_key.name = original_name
        temp_key.value = original_value
    
    # Finally, create the new Basis
    # Deactivate all shape keys
    for k in kb:
        k.value = 0.0
        
    # Activate the new basis key
    new_basis_key.value = 1.0
    
    # Move the current active shape key to the top
    obj.active_shape_key_index = kb.find(key_name)
    bpy.ops.object.shape_key_move(type='TOP')
    
    # Remove the original Basis
    bpy.ops.object.shape_key_remove()
    
    # Create a new Basis from the current shape
    bpy.ops.object.shape_key_add(from_mix=True)
    # Move the last added shape key to the beginning
    bpy.ops.object.shape_key_move(type='TOP')
    # Change the name to Basis
    kb[0].name = 'Basis'
    
    write_log("Shape key basis rebuilt with all dependent keys adjusted")

def remove_shape_key(obj, key_name):
    """Remove a shape key"""
    if not obj.data.shape_keys:
        return
    idx = obj.data.shape_keys.key_blocks.find(key_name)
    if idx != -1:
        obj.active_shape_key_index = idx
        bpy.ops.object.shape_key_remove()

def rename_shape_key(obj, old_name, new_name):
    """Rename a shape key"""
    if not obj.data.shape_keys:
        return
    kb = obj.data.shape_keys.key_blocks
    if old_name in kb:
        kb[old_name].name = new_name

def apply_new_armature_modifier(mesh_obj, arm_obj, report_fn):
    """
    Keep the existing armature modifier and apply a new one.
    
    Parameters:
        mesh_obj: Mesh object
        arm_obj: Armature object
        report_fn: Report function
    """
    # Switch to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Activate the mesh object
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    
    # Do not select the armature object
    arm_obj.select_set(False)
    
    write_log("Adding new armature modifier for application...")
    
    # Add a new armature modifier
    mod = mesh_obj.modifiers.new(name="ArmatureTemp", type='ARMATURE')
    mod.object = arm_obj
    
    # Apply the newly added modifier
    try:
        write_log(f"Applying new armature modifier: {mod.name}")
        bpy.ops.object.modifier_apply(modifier=mod.name)
        print_and_log(report_fn, 'INFO', f"Applied new armature modifier")
    except Exception as e:
        print_and_log(report_fn, 'WARNING', f"Failed to apply modifier: {e}")
        # Continue even on failure
        
    write_log("New armature modifier applied, original modifiers preserved")
    
    return True
