# FireRat Pose Converter

## Overview
**FireRat Pose Converter** is an enhanced Blender addon for copying poses between armatures and applying them as new rest poses. It is designed to handle differences in rest poses (e.g., T-pose to A-pose) and ensures that all associated meshes—including those with complex shape keys—are correctly updated to the new rest state.

This version is a fork of the original T2A Pose Converter, expanded with features like missing bone detection and improved compatibility.

## Features
- **Match Pose & Apply Rest**: Copy a pose from a target armature and bake it as the new rest pose.
- **Add Missing Bones**: Automatically detects bones present in the target but missing in the source, and adds them with correct placement and parenting.
- **Built-in Presets**: Quick-access default Male and Female A-pose presets.
- **Shape Key Preservation**: Advanced logic to rebuild shape keys so they remain functional after the rest pose change.
- **Smart Bone Matching**: Automatically handles common prefix differences (e.g., matching `mixamorig:Hips` to `Hips`).
- **Coexistence Mode**: Designed to run alongside the original T2A plugin without naming conflicts.

## Requirements
- Blender 3.6 or higher

## Installation
1. Download the `Pose_converter` folder or zip.
2. In Blender, go to **Edit** → **Preferences** → **Add-ons**.
3. Click **Install...** and select the zip file, or manually place the folder in your Blender scripts directory.
4. Search for **"FireRat Pose Converter"** and enable it.

## Usage

### Main Conversion
The main workflow is located in the **3D View** → **Tool Shelf (N-panel)** → **FireRat** tab.

1.  **Select Source Armature**: Select the armature you want to modify in the 3D viewport.
2.  **Choose Target Source**:
    *   **Custom**: Select another armature already in your scene.
    *   **Default Male/Female**: Use the included high-quality A-pose references.
3.  **Options**:
    *   **Add Missing Bones**: If enabled, the tool will create any bones found in the target that your source armature is currently missing before matching the pose.
4.  **Execute**: Click **Match Pose & Apply Rest**.

### Utilities
*   **Add Missing Bones**: A standalone button to only add missing bones from the target without changing the current pose.
*   **Apply Current Pose as Rest**: If you've manually posed your character and want to bake that state as the new rest pose (including mesh/shape key updates), use this utility.

## Bone Matching Logic
The addon compares bones by stripping namespace prefixes. For example, `prefix:BoneName` will match `BoneName` or `other_prefix:BoneName`. This makes it highly compatible with Mixamo, VRM, and standard game engine rigs.

## Shape Key Processing
Changing a rest pose usually breaks shape keys. This addon solves that by:
1. Creating a temporary snapshot of the mesh deformation.
2. Applying the new armature rest pose.
3. Re-calculating every shape key's vertex offsets relative to the new basis.
4. Cleaning up temporary data to leave a clean, functional model.

## Credits & License
- **Original Concept**: T2A Pose Converter by CatHut.
- **Enhancements**: Developed by FireRat.
- **License**: MIT License.

---
*Note: Always backup your `.blend` file before performing rest pose operations, as these changes involve complex mesh data rebuilding.*
