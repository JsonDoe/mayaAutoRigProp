# MayaAutoRigProp

**MayaAutoRigProp** is a quick Python-based automation tool for rigging props within Autodesk Maya.
I used it for my student project movie
It's designed to streamline and accelerate rigging workflows in a VFX/animation pipeline by dynamically retrieving assets, rigging them and updating task statuses.

## Features

- **Automated Rigging**: Automatically imports references and geometry, binds them, and configures the scene.
- **ShotGrid Integration**: Uses SGTK and Shotgun API to fetch asset data and update task statuses.
- **Alembic & Maya File Support**: Handles both `.abc` and `.ma` file formats.
- **Smart Namespace and Node Utilities**: Automates naming, node management, and scene clean-up.
- **Scalable Geometry Binding**: Dynamically adjusts controller shapes based on asset dimensions.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/YourUser/MayaAutoRigProp.git
   ```

2. Update your `main.py` to reflect your local path:
   ```python
   tool_path = r"YOUR/LOCAL/PATH/MayaAutoRigProp"
   ```

3. In Maya's Script Editor, run:
   ```python
   import main
   ```

## Usage

The script will:

- Retrieve the current asset and task from ShotGrid.
- Import the latest published `.abc` file (and convert to `.ma`).
- Import a predefined rig reference.
- Bind geometry to the main rig joint.
- Scale and align controllers based on bounding box data.
- Finalize the rig and update the ShotGrid task status.

## Requirements

- Maya 2024+
- `ShotGrid Toolkit (SGTK)` installed and configured
- `shotgun_api3` Python package
- `Frankenstein Tool` (from https://github.com/BaratteG/ for the rig modules logic)

## Notes

- Make sure the environment has access to ShotGrid credentials and API key.
- The `REFERENCE_PATH` in `auto_rig_script.py` should point to a valid reference rig file.
