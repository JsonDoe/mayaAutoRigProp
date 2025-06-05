import maya.cmds as cmds
import maya.api.OpenMaya as om
import os

inToolKit = False

try:
    import sgtk

    inToolKit = True
except:
    pass

hasShotgunAPI = False
try:
    import shotgun_api3

    hasShotgunAPI = True
except:
    pass

shotgrid = None

if inToolKit is True:
    sg = sgtk.platform.current_engine().shotgun
elif hasShotgunAPI is True:
    sg = shotgun_api3.Shotgun(
        "https://p3d.shotgunstudio.com/",
        script_name="ScriptAccessJulienM",
        api_key="XXXXXXXXX",
    )


REFERENCE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..',
                 'modules\\basic_prop_v001.ma'))


def get_current_project_id():
    # Get the current context from the current engine
    engine = sgtk.platform.current_engine()
    if engine is None:
        raise RuntimeError("No ShotGrid Toolkit engine is running.")

    context = engine.context
    if not context.project:
        raise RuntimeError("No project is set in the current context.")

    return context.project['id']


PROJECT_ID = get_current_project_id()


def import_alembic(file_path, namespace="temp"):
    """
    Import an Alembic (.abc) file into the Maya scene.

    :param file_path: The full path to the Alembic file.
    :param namespace: (Optional) Namespace for the imported objects.
    """
    # Check if the Alembic plugin is loaded
    if not cmds.pluginInfo("AbcImport", query=True, loaded=True):
        try:
            cmds.loadPlugin("AbcImport")
        except RuntimeError:
            cmds.error("Failed to load AbcImport plugin.")
            return

    # Construct the Alembic import command
    options = ""
    if namespace:
        options += f"-ns {namespace} "

    try:
        # Import the Alembic file
        cmds.AbcImport(file_path, mode="import")
        print(f"Successfully imported Alembic file: {file_path}")
    except Exception as e:
        cmds.error(f"Failed to import Alembic file: {file_path}\n{str(e)}")


def import_ma(file_path, namespace=":"):
    """
    Import a Maya ASCII (.ma) file into the Maya scene.

    :param file_path: The full path to the Maya ASCII file.
    :param namespace: (Optional) Namespace for the imported objects.
    """
    # Check if the provided file path exists
    if not os.path.exists(file_path):
        cmds.error(f"File does not exist: {file_path}")
        return

    try:
        # If a namespace is provided, create it or ensure it exists
        if namespace:
            if not cmds.namespace(exists=namespace):
                cmds.namespace(add=namespace)

        # Import the .ma file
        cmds.file(file_path, i=True, namespace=namespace)
        print(f"Successfully imported Maya ASCII file: {file_path}")
    except Exception as e:
        cmds.error(f"Failed to import Maya ASCII file: {file_path}\n{str(e)}")


def get_shotgrid_context():
    """Retrieve the ShotGrid context of the currently open scene in Maya."""
    # Get the context using the SGTK API
    try:
        engine = sgtk.platform.current_engine()
        context = engine.context
        return context
    except Exception as e:
        print(f"Error retrieving ShotGrid context: {e}")
        return None


def query_asset_id_from_task():
    """Query the asset ID associated with the current task in Maya."""
    # Get ShotGrid context
    context = get_shotgrid_context()
    if not context:
        print("Failed to retrieve ShotGrid context.")
        return None

    # Check if the context has a task
    if not context.task:
        print("No task found in the current context.")
        return None

    task_id = context.task["id"]
    print(f"Current Task ID: {task_id}")

    # Query the associated asset ID
    try:
        task = sg.find_one("Task", [["id", "is", task_id]], ["entity"])
        if task and task["entity"] and task["entity"]["type"] == "Asset":
            asset_id = task["entity"]["id"]
            print(f"Associated Asset ID: {asset_id}")
            return asset_id
        else:
            print("No associated asset found for the current task.")
            return None
    except Exception as e:
        print(f"Error querying asset ID: {e}")
        return None


def import_alembic_and_select_roots(file_path, namespace="temp"):  # TODELETE
    """
    Import an Alembic (.abc) file into the Maya scene and select its root nodes

    :param file_path: The full path to the Alembic file.
    :param namespace: (Optional) Namespace for the imported objects.
    """
    # Check if the Alembic plugin is loaded
    if not cmds.pluginInfo("AbcImport", query=True, loaded=True):
        try:
            cmds.loadPlugin("AbcImport")
        except RuntimeError:
            cmds.error("Failed to load AbcImport plugin.")
            return

    # List of scene nodes before import
    nodes_before = cmds.ls(dag=True, long=True)

    try:
        # Import the Alembic file
        cmds.AbcImport(file_path, mode="import", connect=False)
        print(f"Successfully imported Alembic file: {file_path}")
    except Exception as e:
        cmds.error(f"Failed to import Alembic file: {file_path}\n{str(e)}")
        return

    # List of scene nodes after import
    nodes_after = cmds.ls(dag=True, long=True)

    # Identify new root nodes (nodes that were added by the import)
    imported_nodes = set(nodes_after) - set(nodes_before)
    root_nodes = [
        node for node in imported_nodes if cmds.listRelatives(
            node, parent=True) is None
    ]

    # Apply namespace, if provided
    if namespace:
        for root in root_nodes:
            new_name = f"{namespace}:{root}"
            cmds.rename(root, new_name)

    # Select the root nodes
    if root_nodes:
        cmds.select(root_nodes, replace=True)
        print(f"Selected root nodes: {root_nodes}")
    else:
        print("No root nodes found from Alembic import.")


def get_last_published_alembic(asset_id):
    """
    Retrieve the last 'PublishedFile' of type 'Alembic Cache' from the UV task
    of a given asset.

    Args:
        asset_id (int): The ID of the asset in ShotGrid.

    Returns:
        dict: The latest PublishedFile record, or None if not found.
    """
    # Connect to ShotGrid

    try:
        # Find the UV Task associated with the asset
        uv_task = sg.find_one(
            "Task",
            [["entity.Asset.id", "is", asset_id], ["content", "is", "UV"]],
            ["id", "content"],
        )

        if not uv_task:
            print(f"No UV task found for Asset ID {asset_id}.")
            return None

        print(f"Found UV Task: {uv_task}")

        # Query PublishedFiles for the UV task
        # filtered by type "Alembic Cache"
        published_files = sg.find(
            "PublishedFile",
            [
                ["task.Task.id", "is", uv_task["id"]],
                ["published_file_type.PublishedFileType.code",
                 "is", "Alembic Cache"],
            ],
            ["id", "code", "created_at", "path"],
        )

        if not published_files:
            print(
                "No 'Alembic Cache' PublishedFiles found"
                f" for UV Task ID {uv_task['id']}."
            )
            return None

        # Sort the results by created_at to get the latest file
        latest_published_file = sorted(
            published_files, key=lambda x: x["created_at"], reverse=True
        )[0]
        print(f"Latest 'Alembic Cache' PublishedFile: {latest_published_file}")
        return latest_published_file

    except Exception as e:
        print(f"Error querying PublishedFiles: {e}")
        return None


def select_nodes_in_namespace(namespace: str = "TEMP"):
    """
    Select all nodes belonging to a given namespace.

    :param namespace: The namespace to search for nodes.
    """
    if not namespace:
        cmds.error("Please provide a valid namespace.")
        return

    # List all nodes in the namespace
    nodes_in_namespace = cmds.ls(f"{namespace}:*", long=True)

    if not nodes_in_namespace:
        cmds.warning(f"No nodes found in namespace: {namespace}")
        return

    # Select all nodes in the namespace
    cmds.select(nodes_in_namespace, replace=True)
    print(f"Selected nodes in namespace '{namespace}': {nodes_in_namespace}")


def create_and_set_namespace(namespace_name="TEMP"):
    """
    Create a namespace and set it as the current namespace in Maya.
    If the namespace already exists, it will simply set it as the current one.

    :param namespace_name: The name of the namespace to create and set
    (default is 'TEMP').
    """
    # Check if the namespace already exists
    if not cmds.namespace(exists=namespace_name):
        # Create the namespace if it doesn't exist
        cmds.namespace(add=namespace_name)
        print(f"Namespace '{namespace_name}' created.")
    else:
        print(f"Namespace '{namespace_name}' already exists.")

    # Set the current namespace
    cmds.namespace(set=namespace_name)
    print(f"Current namespace set to: {namespace_name}")


def delete_namespace(namespace_name=":TEMP", move_nodes_to_root=True):
    """
    Delete a namespace in Maya and set the namespace back to the root
    namespace.

    :param namespace_name: The name of the namespace to delete
    (default is 'TEMP').
    :param move_nodes_to_root: Whether to move nodes to the root namespace
    before deletion.
    """
    # Check if the namespace exists
    if not cmds.namespace(exists=namespace_name):
        cmds.warning(f"Namespace '{namespace_name}' does not exist.")
        return

    # Move nodes to root namespace if required
    if move_nodes_to_root:
        nodes_in_namespace = cmds.ls(f"{namespace_name}:*", long=True)
        for node in nodes_in_namespace:
            # Rename the node to remove the namespace
            new_name = cmds.rename(node, node.split(":")[-1])
            print(f"Moved '{node}' to root as '{new_name}'.")

    # Delete the namespace
    try:
        cmds.namespace(
            removeNamespace=namespace_name, mergeNamespaceWithRoot=True)
        print(f"Namespace '{namespace_name}' has been deleted.")
    except Exception as e:
        cmds.error(f"Failed to delete namespace '{namespace_name}': {e}")

    # Set the current namespace back to root ('')
    cmds.namespace(set=":")
    print("Namespace has been set back to the root (':').")


def select_highest_parents():
    """
    Select only the highest parent nodes from the current selection in Maya.
    """
    # Get the current selection
    selection = cmds.ls(selection=True, long=True)

    if not selection:
        cmds.warning("No objects selected.")
        return

    # Find the highest parent nodes
    highest_parents = []
    for obj in selection:
        parent = cmds.listRelatives(obj, parent=True, fullPath=True)
        if not parent:
            # If there's no parent, this is a top-level node
            highest_parents.append(obj)
        elif parent[0] not in selection:
            # If the parent isn't in the selection, this is a highest parent
            highest_parents.append(obj)

    # Remove duplicates and re-select only the highest parents
    highest_parents = list(set(highest_parents))
    cmds.select(highest_parents, replace=True)
    print(f"Selected highest parent nodes: {highest_parents}")


def update_task_status_to_pending_review(asset_id):
    """
    Update the status of the Rig Task for an asset to "Pending Review".

    Args:
        asset_id (int): The ID of the asset in ShotGrid.

    Returns:
        bool: True if the task was successfully updated, False otherwise.
    """
    # Connect to ShotGrid

    try:
        # Find the Rig Task associated with the asset
        rig_task = sg.find_one(
            "Task",
            [["entity.Asset.id", "is", asset_id], ["content", "is", "Rig"]],
            ["id", "content", "sg_status_list"],
        )

        if not rig_task:
            print(f"No Rig Task found for Asset ID {asset_id}.")
            return False

        print(f"Found Rig Task: {rig_task}")

        # Update the task status to "Pending Review"
        # Replace "rev" with your ShotGrid's status code for "Pending Review"
        updated_task = sg.update(
            "Task", rig_task["id"], {"sg_status_list": "rev"})
        print(f"Updated Task: {updated_task}")
        return True

    except Exception as e:
        print(f"Error updating task status: {e}")
        return False


def get_highest_bounding_box_distance(geo_list):
    """
    Calculates the combined bounding box of all specified objects in Maya 
    and returns the highest distance between the X and Z axes (ignoring Y).

    Args:
        geo_list (list): List of geometry (transform or shape) node names.

    Returns:
        float: The highest distance between X and Z axes.
    """
    if not geo_list:
        cmds.warning("No objects provided. Please provide a list of geometry "
                     "names.")
        return None

    # Initialize min/max values
    min_x, min_y, min_z = float("inf"), float("inf"), float("inf")
    max_x, max_y, max_z = float("-inf"), float("-inf"), float("-inf")

    # Iterate over each object in the provided list
    for obj in geo_list:
        if not cmds.objExists(obj):
            cmds.warning(f"Object '{obj}' does not exist.")
            continue

        bbox = cmds.exactWorldBoundingBox(obj)

        # Expand the bounding box to include this object's bounding box
        min_x = min(min_x, bbox[0])
        min_y = min(min_y, bbox[1])
        min_z = min(min_z, bbox[2])
        max_x = max(max_x, bbox[3])
        max_y = max(max_y, bbox[4])
        max_z = max(max_z, bbox[5])

    # Calculate distances (max - min) for X and Z
    distance_x = max_x - min_x
    distance_z = max_z - min_z

    # Return the highest distance between X and Z
    return max(distance_x, distance_z)


def update_offset_matrix(node, scale_x, scale_y, scale_z):
    """
    Updates the offsetMatrix attribute of a given shape node to fit the desired
    scale. Additionally, sets Translate Y to scale_y / 2.

    Args:
        node (str): Name of the transform or shape node.
        scale_x (float): Desired scale in X direction.
        scale_y (float): Desired scale in Y direction.
        scale_z (float): Desired scale in Z direction.
    """
    if not cmds.objExists(node):
        cmds.warning(f"Node '{node}' does not exist.")
        return

    # Get shape node if a transform is given
    if cmds.objectType(node) == "transform":
        shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
        if not shapes:
            cmds.warning(f"Transform '{node}' has no shape node.")
            return
        shape_node = shapes[0]  # Use the first shape node
    else:
        shape_node = node  # Assume it's already a shape node

    # Check if offsetMatrix exists, otherwise create it
    if not cmds.attributeQuery("offsetMatrix", node=shape_node, exists=True):
        cmds.addAttr(shape_node, longName="offsetMatrix", dataType="matrix")

    # Get current offsetMatrix
    current_matrix = cmds.getAttr(shape_node + ".offsetMatrix")

    # Convert to OpenMaya matrix
    matrix = om.MMatrix(current_matrix)

    # Create scale matrix
    scale_matrix = om.MMatrix([
        [scale_x, 0, 0, 0],
        [0, scale_y, 0, 0],
        [0, 0, scale_z, 0],
        [0, scale_y / 2, 0, 1]  # Translate Y is scale_y / 2
    ])

    # Apply scaling and translation
    new_matrix = matrix * scale_matrix

    # Set updated offsetMatrix
    cmds.setAttr(shape_node + ".offsetMatrix", list(new_matrix), type="matrix")

    print(f"Updated offsetMatrix for {shape_node} with scale ({scale_x}, "
          f"{scale_y}, {scale_z}) and Translate Y = {scale_y / 2}")


def is_camera(node):
    """
    Checks if the given transform node is a camera.

    Args:
        node (str): The name of the transform node.

    Returns:
        bool: True if the node is a camera, False otherwise.
    """
    if not cmds.objExists(node):
        cmds.warning(f"Node '{node}' does not exist.")
        return False

    # Get all child shapes of the node
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []

    # Check if any of the child shapes are cameras
    for shape in shapes:
        if cmds.nodeType(shape) == "camera":
            return True

    return False


def has_objectType(node):
    """
    Checks if the given node has the attribute 'rig_objectType'.

    Args:
        node (str): The name of the Maya node to check.

    Returns:
        bool: True if the attribute exists, False otherwise.
    """
    if not cmds.objExists(node):
        cmds.warning(f"Node '{node}' does not exist.")
        return False

    if cmds.attributeQuery("rig_objectType", node=node, exists=True) or \
            cmds.attributeQuery("pip_groupType", node=node, exists=True):
        return True
    return False


def bind_skin_like_maya(node_list):
    """
    Mimics Maya's "Bind Skin" button behavior. Automatically detects meshes and
    joints from the provided node list and binds them.

    Args:
        node_list (list): List of nodes (geometry and joints) to process.
    """
    if not node_list:
        cmds.warning(
            "No nodes provided. Please provide a list of mesh and joint nodes."
            )
        return

    meshes = []
    joints = []

    # Sort the node list into meshes and joints
    for obj in node_list:
        if cmds.nodeType(obj) == "joint":
            joints.append(obj)
        elif cmds.listRelatives(obj, shapes=True, noIntermediate=True) and \
                cmds.objectType(
                    cmds.listRelatives(obj, shapes=True)[0]) == "mesh":
            meshes.append(obj)

    # Ensure both meshes and joints are present
    if not meshes:
        cmds.warning("No valid meshes found in the provided nodes.")
        return
    if not joints:
        cmds.warning("No valid joints found in the provided nodes.")
        return

    # Bind each mesh to all selected joints using default Maya settings
    for mesh in meshes:
        skin_cluster = cmds.skinCluster(
            joints, mesh,
            toSelectedBones=True,  # Similar to default Bind Skin behavior
            bindMethod=0,  # Closest distance
            normalizeWeights=1,  # Interactive normalization
            skinMethod=0,  # Classic linear skinning
            maximumInfluences=4,  # Default influence limit
            dropoffRate=4.0,  # Default dropoff rate
            name=f"{mesh}_skinCluster"
        )[0]

        print(f"SkinCluster '{skin_cluster}' created for mesh '{mesh}' with "
              f"joints {joints}")


def get_all_geo_from_scene():
    """
    Returns a list of all geometry objects in the scene.

    Returns:
        list: A list of geometry node names (excluding cameras and nodes with
              'rig_objectType' attribute).
    """
    return [node for node in cmds.ls() if cmds.nodeType(node) == "transform"
            and not has_objectType(node)
            and not is_camera(node)]


def bind_all_geo_to_main_joint(
        main_joint="main_JNT", local_controller="local_FK_CON",
        global_controller="global_FK_CON"):
    """
    Binds all geometry in the scene to the provided main joint using the
    specified controllers for offset.

    Args:
        main_joint (str): Name of the main joint to bind the geometry to.
        local_controller (str): Name of the local controller.
        global_controller (str): Name of the global controller.
    """
    geo = get_all_geo_from_scene()
    bounding_scale = get_highest_bounding_box_distance(geo)

    local_bouding_scale = bounding_scale * 0.85
    # Update the offset matrix for the controllers
    update_offset_matrix(local_controller + "Shape", local_bouding_scale,
                         local_bouding_scale / 10, local_bouding_scale)
    update_offset_matrix(global_controller + "Shape", bounding_scale,
                         bounding_scale / 20, bounding_scale)

    # Append the main joint to the geometry list for binding
    to_bind = geo
    to_bind.append(main_joint)
    bind_skin_like_maya(to_bind)
    cmds.select(cl=True)
    print("All geometry bound to the main joint.")


def update_task_status_to_final(asset_id):
    """
    Update the status of the Rig Task for an asset to "Final".

    Args:
        asset_id (int): The ID of the asset in ShotGrid.

    Returns:
        bool: True if the task was successfully updated, False otherwise.
    """
    # Connect to ShotGrid
    try:
        # Find the Rig Task associated with the asset
        rig_task = sg.find_one(
            "Task",
            [["entity.Asset.id", "is", asset_id], ["content", "is", "Rig"]],
            ["id", "content", "sg_status_list"],
        )

        if not rig_task:
            print(f"No Rig Task found for Asset ID {asset_id}.")
            return False

        print(f"Found Rig Task: {rig_task}")

        # Update the task status to "Final"
        # Replace "fin" with your ShotGrid's status code for "Final"
        updated_task = sg.update(
            "Task", rig_task["id"], {"sg_status_list": "fin"})
        print(f"Updated Task to Final: {updated_task}")
        return True

    except Exception as e:
        print(f"Error updating task status to Final: {e}")
        return False


def get_highest_node_from(start_node):
    """
    Select the highest node in the hierarchy starting from a specific node.

    Args:
        start_node (str): The name of the node from which to start searching.
    """
    # Check if the node exists
    if not cmds.objExists(start_node):
        cmds.error(f"Node '{start_node}' does not exist.")
        return

    # Get the parent node of the start node
    parent_node = cmds.listRelatives(start_node, parent=True)

    # If there is no parent node, the start node is already the highest node
    if not parent_node:
        print(f"'{start_node}' is already the highest node.")
        cmds.select(start_node)
        return start_node

    # Traverse up the hierarchy until the root is reached (node with no parent)
    highest_node = start_node
    while parent_node:
        highest_node = parent_node[0]
        parent_node = cmds.listRelatives(highest_node, parent=True)

    # Select the highest node
    return highest_node


def verify_and_rename_node(node_name, new_name):
    """
    Verifies if the name of the given node matches the entered name.
    If not, renames the node to the entered name.

    Args:
        node_name (str): The current name of the node.
        new_name (str): The desired name to compare against and rename the
        node if different.
    """
    # Check if the node exists
    if not cmds.objExists(node_name):
        cmds.error(f"Node '{node_name}' does not exist.")
        return

    # Get the current name of the node
    current_name = node_name

    # Check if the current name matches the new name
    if current_name != new_name:
        try:
            # Rename the node
            cmds.rename(current_name, new_name)
            print(f"Node '{current_name}' renamed to '{new_name}'.")
        except Exception as e:
            cmds.error(f"Failed to rename node: {e}")
    else:
        print(
            f"Node '{current_name}' already has the desired name '{new_name}'."
            )


def clean_scene(main_joint="main_JNT",
                rig_group="rig_RIG",
                module_name="module",
                asset_name="asset_name"):

    cmds.setAttr(main_joint + ".visibility", 0)
    cmds.parent(module_name, rig_group)
    asset_node = get_highest_node_from(module_name)
    verify_and_rename_node(asset_node, asset_name)


def auto_rig_prop():
    asset_id = query_asset_id_from_task()
    if asset_id:
        print(f"Asset ID: {asset_id}")
        latest_file = get_last_published_alembic(asset_id)
        print(f"Latest Alembic Cache PublishedFile: {latest_file}")
        if latest_file["path"]["local_path_windows"]:
            print(latest_file["path"]["local_path_windows"])
            import_ma(REFERENCE_PATH)
            # create_and_set_namespace()
            clean_path = latest_file["path"]["local_path_windows"].replace(
                ".abc", ".ma")
            ma_path = clean_path.replace("_LO", "")
            ma_path = ma_path.replace("_MI", "")
            ma_path = ma_path.replace("_HI", "")
            import_ma(ma_path)
            bind_all_geo_to_main_joint()
            name = str(latest_file["code"]).split("_")[1]
            clean_scene(asset_name=name)
            success = update_task_status_to_final(asset_id)
            if success:
                print("Task status successfully updated to 'final'.")
            else:
                print("Failed to update task status.")
            cmds.select(name)
