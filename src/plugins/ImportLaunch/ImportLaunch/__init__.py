"""
This is where the implementation of the plugin code goes.
The ImportLaunch-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('ImportLaunch')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class ImportLaunch(PluginBase):
  def main(self):
    core = self.core
    active_node = self.active_node
    logger = self.logger
    
    # Hardcoded structure based on the provided JSON
    launch_data = launch_data = {
      "tag": "launch",
      "attributes": {},
      "children": [
        {
          "tag": "argument",
          "attributes": {
            "name": "negativeOne",
            "value": "-1"
          },
          "children": []
        },
        {
          "tag": "node",
          "attributes": {
            "name": "argNumber",
            "pkg": "number",
            "type": "argNumber.py",
            "args": "$(arg negativeOne)"
          },
          "children": []
        },
        {
          "tag": "node",
          "attributes": {
            "name": "three",
            "pkg": "number",
            "type": "three.py"
          },
          "children": []
        },
        {
          "tag": "node",
          "attributes": {
            "name": "multiply",
            "pkg": "operations",
            "type": "multiply"
          },
          "children": [
            {
              "tag": "remap",
              "attributes": {
                "from": "product",
                "to": "dividend"
              },
              "children": []
            }
          ]
        },
        {
          "tag": "node",
          "attributes": {
            "name": "divide",
            "pkg": "operations",
            "type": "divide"
          },
          "children": []
        },
        {
          "tag": "remap",
          "attributes": {
            "from": "number",
            "to": "multiply1"
          },
          "children": []
        },
        {
          "tag": "remap",
          "attributes": {
            "from": "three",
            "to": "multiply2"
          },
          "children": []
        },
        {
          "tag": "remap",
          "attributes": {
            "from": "quotient",
            "to": "display"
          },
          "children": []
        },
        {
          "tag": "include",
          "attributes": {
            "name": "display.launch"
          },
          "children": []
        },
        {
          "tag": "group",
          "attributes": {
            "name": "denominator"
          },
          "children": [
            {
              "tag": "node",
              "attributes": {
                "name": "four",
                "pkg": "number",
                "type": "four.py"
              },
              "children": []
            },
            {
              "tag": "node",
              "attributes": {
                "name": "two",
                "pkg": "number",
                "type": "two.py"
              },
              "children": []
            },
            {
              "tag": "node",
              "attributes": {
                "name": "add",
                "pkg": "operations",
                "type": "add"
              },
              "children": []
            },
            {
              "tag": "remap",
              "attributes": {
                "from": "four",
                "to": "add1"
              },
              "children": []
            },
            {
              "tag": "remap",
              "attributes": {
                "from": "two",
                "to": "add2"
              },
              "children": []
            },
            {
              "tag": "remap",
              "attributes": {
                "from": "sum",
                "to": "divisor"
              },
              "children": []
            }
          ]
        }
      ]
    }
    meta_types = ["LaunchFile", "Include", "Argument", "Remap", "Group", "Parameter", "rosparam", "Node", "Topic", "GroupPublisher", "GroupSubscriber", "Subscriber", "Publisher"]

    def get_type(node):
        base_type = core.get_base(node)
        while base_type and core.get_attribute(base_type, 'name') not in meta_types:
            base_type = core.get_base(base_type)
        return core.get_attribute(base_type, 'name')

    # Ensure 'LaunchFile' type exists in the META
    if 'LaunchFile' not in self.META:
      logger.error('LaunchFile type not found in META. Ensure it exists in the meta-model.')
      return

    try:
      # Define parameters for the new LaunchFile node
      params = {
        'parent': active_node,
        'base': self.META['LaunchFile']
      }
      launch_file_node = core.create_node(params)
      core.set_attribute(launch_file_node, 'name', 'launch')
      logger.info(f'Created new LaunchFile node with name: "launch".')
      
      # Load the Node Library for comparison
      all_children = core.load_sub_tree(active_node)
      node_lib = next((child for child in all_children if core.get_attribute(child, "name") == "NodeLibrary"), None)

      if not node_lib:
        logger.error("NodeLibrary not found.")
        return

      # Cache all nodes in the library
      lib_children = core.load_sub_tree(node_lib)
      node_library = {
        (core.get_attribute(node, "pkg"), core.get_attribute(node, "type")): node
        for node in lib_children
        if core.get_attribute(node, "pkg") and core.get_attribute(node, "type")
      }

      def find_node_in_library(node_data):
        pkg = node_data.get("attributes", {}).get("pkg")
        node_type = node_data.get("attributes", {}).get("type")
        return node_library.get((pkg, node_type))
      
      def copy_attributes_and_pub_sub(existing_node, child_node):
        """
        Copies all attributes and publishers/subscribers from the existing library node to the new child node.
        """
        # Copy all attributes from the library node to the new node
        for attr in core.get_attribute_names(existing_node):
          core.set_attribute(child_node, attr, core.get_attribute(existing_node, attr))

        # Load publishers and subscribers from the library node
        lib_children = core.load_sub_tree(existing_node)
        new_node_children = core.load_children(child_node)

        def child_exists(child, children):
          """Check if a child with the same name already exists in the new node."""
          child_name = core.get_attribute(child, "name")
          return any(core.get_attribute(existing_child, "name") == child_name for existing_child in children)

        for lib_child in lib_children:
          child_type = get_type(lib_child)
          if child_type in ["Publisher", "Subscriber"]:
            if not child_exists(lib_child, new_node_children):
              copied_node = core.copy_node(lib_child, child_node)
              logger.info(f"Copied {core.get_attribute(copied_node, 'name')} to {core.get_attribute(child_node, 'name')}.")


      def create_child_nodes(parent_node, data):
        """
        Creates child nodes using attributes from the input data if the node does not exist in the library.
        """
        for child in data.get("children", []):
          tag = child.get("tag").capitalize()
          attributes = child.get("attributes", {})
          name_attribute = attributes.get("name")
          
          # Check if the node already exists in the library
          existing_node = find_node_in_library(child)
          
          if existing_node:
            logger.info(f"Node {name_attribute} found in library. Copying attributes and publishers/subscribers.")
            child_node = core.create_child(parent_node, core.get_meta_type(existing_node))
            copy_attributes_and_pub_sub(existing_node, child_node)
          else:
            # Create new node if not found in the library
            child_node = core.create_child(parent_node, self.META.get(tag, None) if tag in self.META else None)
            logger.info(f"Created new node: {name_attribute} with attributes from input.")
            
            for attr, value in attributes.items():
              core.set_attribute(child_node, attr, value)
              
            # Add a publisher for the 'pkg' attribute if it exists
            if "pkg" in attributes:
              existing_publishers = [
                core.get_attribute(existing_child, "name")
                for existing_child in core.load_children(child_node)
                if get_type(existing_child) == "Publisher"
              ]
              if attributes["pkg"] not in existing_publishers:
                publisher_node = core.create_child(child_node, self.META["Publisher"])
                core.set_attribute(publisher_node, "name", attributes["pkg"])
                logger.info(f"Added publisher: {attributes['pkg']} to node {name_attribute}.")
                
          # Recursively handle child nodes
          create_child_nodes(child_node, child)

      # Create child nodes from launch_data
      create_child_nodes(launch_file_node, launch_data)

      # Save the changes
      new_commit_hash = self.util.save(launch_file_node, self.commit_hash)
      self.project.set_branch_hash(
        branch_name=self.branch_name,
        new_hash=new_commit_hash["hash"],
        old_hash=self.commit_hash
      )
      logger.info("All nodes successfully created and saved.")
    except Exception as e:
      logger.error(f"Error during node creation: {str(e)}")
