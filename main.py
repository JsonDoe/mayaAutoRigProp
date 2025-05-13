import sys
import importlib


# Add your tool path
tool_path = r"C:/Users/julien.miternique/Documents/workspace/mayaAutoRigProp"
if tool_path not in sys.path:
    sys.path.append(tool_path)

# Reload both modules
import logic.auto_rig_script_update

importlib.reload(logic.auto_rig_script_update)

from logic.auto_rig_script_update import auto_rig_prop

auto_rig_prop()
