# RigX Validation System

A comprehensive validation framework for Maya rigging workflows.

## Directory Structure

```
Validator/
├── CheckIn/          # Model validation modules (cleanup before rigging)
├── CheckOut/         # Rig validation modules (cleanup before delivery)
└── Presets/          # Validation presets for different workflows
```

## Available Validation Modules

### Model Validation (CheckIn)
These modules clean up the model before rigging:

- **FreezeTransform** - Checks and freezes non-zero transforms
- **GeometryHistory** - Removes construction history
- **DuplicatedName** - Finds and fixes duplicate names
- **NamespaceCleaner** - Removes custom namespaces
- **VaccineCleaner** - Detects and removes malicious script nodes
- **UnlockAttributes** - Unlocks locked attributes

### Rig Validation (CheckOut)
These modules clean up the rig before delivery:

- **CycleChecker** - Checks for connection cycles
- **BrokenRivet** - Finds and fixes broken rivets (follicles at origin)
- **KeyframeCleaner** - Removes unnecessary keyframes
- **DisplayLayers** - Removes unnecessary display layers
- **HideAllJoints** - Hides visible joints

## Presets

- **default.json** - Enables all validation modules
- **model_only.json** - Enables only model validation modules
- **rig_only.json** - Enables only rig validation modules

## Usage in Maya

### Launch the Tool
```python
import rigging_pipeline.tools.rigx_riggingValidator as validator
validator.show_rigging_validator()
```

### Use Different Presets
```python
# Load a specific preset
validator = RiggingValidator()
validator.apply_preset("model_only")  # or "rig_only" or "default"
```

### Run Validations
```python
# Run all enabled validations
results = validator.run_all_validations()

# Run specific modules
results = validator.run_validation(["FreezeTransform", "GeometryHistory"], mode="check")

# Fix issues
results = validator.run_validation(["FreezeTransform"], mode="fix")
```

## Adding New Validation Modules

1. Create a new Python file in the appropriate directory (`CheckIn/` or `CheckOut/`)
2. Follow the module template:

```python
"""
ModuleName Validation Module
Brief description of what it does
"""

DESCRIPTION = "Detailed description for the UI"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Your validation logic here
    # mode can be "check" or "fix"
    # objList is optional list of objects to check
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": number_of_objects_checked,
        "total_issues": len(issues)
    }
```

3. Add the module to the appropriate preset files
4. The module will automatically appear in the UI

## Module Categories

- **Model (CheckIn)**: Cleanup modules for model preparation
- **Rig (CheckOut)**: Cleanup modules for rig preparation

## Troubleshooting

- **No validations showing**: Make sure the `Validator` directory exists and contains validation modules
- **Import errors**: Ensure Maya is running and the rigging_pipeline package is in your Python path
- **Empty results**: Check if the scene has objects to validate, or if you're in a referenced scene

## Validation Order

The system runs validations in a recommended order:
1. **Model validations** first (cleanup)
2. **Rig validations** second (preparation)

This ensures that the model is clean before rigging begins.
