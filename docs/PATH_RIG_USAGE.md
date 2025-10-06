# Path Rigging System - Usage Guide

## Overview

The improved path rigging system provides a flexible and robust way to create rigs that follow curves. It supports user-provided curves and offers extensive customization options.

## Key Improvements

### 1. User Curve Input
- **Before**: Hardcoded `tmpCrv` curve
- **After**: Accepts any user-provided curve or prompts for selection

### 2. Better Error Handling
- Validates curve inputs
- Provides clear error messages
- Cleans up failed creations

### 3. Modular Design
- Separated into logical functions
- Easy to customize and extend
- Better code organization

### 4. Enhanced Functionality
- Configurable joint count and curve spans
- Optional control creation
- Surface binding support
- Custom naming prefixes

## Usage Examples

### Basic Usage

```python
import maya.cmds as mc
from rigging_pipeline.utils.rigx_pathRig_improved import create_path_rig

# Create a path rig from selected curve
result = create_path_rig_from_selection()

# Or specify a curve directly
result = create_path_rig(input_curve="myCurve")
```

### Advanced Usage

```python
# Create a custom path rig
result = create_path_rig(
    input_curve="spine_curve",
    num_joints=25,
    curve_spans=40,
    surface="character_mesh",
    joint_prefix="spine_jnt",
    control_prefix="spine_ctrl",
    create_controls=True,
    auto_orient=True
)
```

### Using the UI

```python
from rigging_pipeline.utils.rigx_pathRig_improved import show_path_rig_ui

# Open the path rig creator UI
show_path_rig_ui()
```

## Function Parameters

### `create_path_rig()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_curve` | str | None | Name of input curve (prompts if None) |
| `num_joints` | int | 30 | Number of joints along the path |
| `curve_spans` | int | 50 | Number of spans for curve rebuilding |
| `surface` | str | None | Surface to bind joints to |
| `joint_prefix` | str | "jnt_path" | Prefix for joint names |
| `control_prefix` | str | "Ctrl_path" | Prefix for control names |
| `create_controls` | bool | True | Whether to create control curves |
| `auto_orient` | bool | True | Whether to auto-orient joints |

## Return Value

The function returns a dictionary containing all created objects:

```python
{
    'main_group': 'sys_pathRig',
    'joint_chain': ['jnt_path1', 'jnt_path2', ...],
    'object_joints': ['jnt_pathObj1', 'jnt_pathObj2', ...],
    'secondary_joints': ['sj_jnt_path1', 'sj_jnt_path2', ...],
    'curve_system': {
        'path_curve': 'crv_path',
        'object_curve': 'crv_pathObj'
    },
    'control_system': {
        'control_group': 'grp_pathCtrls',
        'controls': ['Ctrl_path0', 'Ctrl_path1', ...]
    },
    'ik_system': ['ikH_path', 'ikH_obj']
}
```

## Workflow

1. **Prepare your curve**: Create or select a NURBS curve
2. **Optional**: Select a surface for binding
3. **Run the function**: Use `create_path_rig()` or the UI
4. **Customize**: Adjust the created controls and attributes
5. **Animate**: Use the percent attribute on the curve to animate along the path

## Tips

- Use the `percent` attribute on the path curve to control position along the path
- The system creates both path and object curves for flexible control
- Secondary joints are automatically created for skinning
- Controls are created for each CV of the curve for fine manipulation

## Troubleshooting

### Common Issues

1. **"Invalid curve" error**: Make sure the object is a valid NURBS curve
2. **"Object doesn't exist" error**: Check that the curve name is correct
3. **Skinning fails**: Ensure the surface is a valid mesh object

### Error Recovery

The system automatically cleans up failed creations. If something goes wrong:
1. Check the error message
2. Verify your inputs
3. Try again with corrected parameters

## Legacy Compatibility

The original `devpath()` function is still available for backward compatibility:

```python
# Old way (still works)
result = devpath(self, noj=30, spn=50)

# New way (recommended)
result = create_path_rig(num_joints=30, curve_spans=50)
```
