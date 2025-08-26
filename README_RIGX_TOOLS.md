# RigX Tools

A new modular tool system for the RigX rigging pipeline that provides a clean, extensible interface for various rigging utilities.

## Overview

RigX Tools is designed as a centralized hub for multiple rigging tools, each with its own functionality and purpose. The tool provides a modern, user-friendly interface that follows the established RigX design patterns.

## Features

### Core Functionality
- **Modular Design**: Easy to add new tools and functionality
- **Consistent UI**: Follows RigX design patterns and theming
- **Selection Management**: Multiple selection modes (Selected, Hierarchy, All)
- **Object Filtering**: Filter by object types (joints, meshes, transforms, etc.)
- **Status Monitoring**: Real-time status updates and feedback
- **Error Handling**: Comprehensive error handling with user feedback

### Available Tools

#### Tool 1 (Green)
- **Purpose**: Process selected objects with advanced operations
- **Functionality**: Analyzes selected objects and performs operations
- **Use Case**: General object processing and analysis

#### Tool 2 (Blue)
- **Purpose**: Advanced rigging automation tool
- **Functionality**: Automated rigging processes
- **Use Case**: Complex rigging automation tasks

#### Tool 3 (Orange)
- **Purpose**: Utility tool for common rigging tasks
- **Functionality**: Common rigging operations and utilities
- **Use Case**: Daily rigging workflow tasks

## Installation

1. Ensure the tool files are in the correct directory structure:
   ```
   src/rigging_pipeline/tools/rigx_tools.py
   src/rigging_pipeline/tools/ui/rigx_tools_ui.py
   ```

2. The tool is automatically imported when importing the tools module:
   ```python
   from rigging_pipeline.tools import rigx_tools
   ```

## Usage

### Basic Usage
```python
from rigging_pipeline.tools.rigx_tools import RigXTools

# Create an instance
tools = RigXTools()

# Show the UI
tools.show_ui()
```

### Programmatic Tool Execution
```python
# Execute specific tools
tools.run_tool_1()  # Process selected objects
tools.run_tool_2()  # Run automation tool
tools.run_tool_3()  # Execute utility tool
```

### Maya Integration
The tool automatically integrates with Maya's main window and follows Maya's UI conventions.

## UI Components

### Tool Selection Panel
- Three main tool buttons with distinct colors and descriptions
- Each tool has its own functionality and purpose
- Clear visual feedback and status updates

### Options Panel
- **Selection Mode**: Choose between Selected, Hierarchy, or All objects
- **Object Type Filter**: Filter objects by type (joints, meshes, transforms, etc.)

### Status Panel
- Real-time status updates
- Color-coded status indicators (Green: Success, Orange: Warning, Red: Error, Blue: Processing)

### Action Buttons
- **Refresh**: Update status and selection information
- **Close**: Close the tool window

## Customization

### Adding New Tools
1. Add new tool methods to the `RigXTools` class
2. Update the UI to include new tool buttons
3. Implement the tool functionality

### Modifying Existing Tools
1. Edit the tool methods in `rigx_tools.py`
2. Update the UI elements in `rigx_tools_ui.py`
3. Test the changes thoroughly

### Styling
The tool uses the centralized RigX theme system. Customize colors and styles by modifying the `THEME_STYLESHEET` or individual button styles.

## Dependencies

- Maya (for Maya-specific functionality)
- PySide2 (for UI components)
- RigX pipeline modules (for theming and utilities)

## File Structure

```
rigx_tools.py          # Main tool class and functionality
ui/
  rigx_tools_ui.py    # UI implementation and layout
```

## Testing

Use the provided test script to verify the tool functionality:

```bash
python test_rigx_tools.py
```

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure the tool files are in the correct directory structure
2. **UI Not Showing**: Check Maya integration and PySide2 installation
3. **Tool Execution Errors**: Verify Maya commands and object selection

### Debug Mode
Enable debug output by setting environment variables or modifying the tool code.

## Future Enhancements

- **Plugin System**: Allow external tools to register with the system
- **Tool Presets**: Save and load tool configurations
- **Batch Processing**: Execute multiple tools in sequence
- **Custom Tool Creation**: UI for creating new tools without coding
- **Tool History**: Track and replay tool operations

## Contributing

When adding new tools or modifying existing ones:
1. Follow the established code patterns
2. Maintain consistent error handling
3. Update documentation
4. Test thoroughly in Maya environment

## License

This tool is part of the RigX pipeline and follows the same licensing terms.
