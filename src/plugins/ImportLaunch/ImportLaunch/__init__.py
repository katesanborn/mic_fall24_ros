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
    logger.info(active_node)
    
    # Hardcoded structure based on the provided JSON
    launch_data = launch_data = {
      "tag": "launch",
      "attributes": {},
      "children": [
        {
          "tag": "Argument",
          "attributes": {
            "name": "negativeOne",
            "value": "-1"
          },
          "children": [],
          "metatype": "Argument",
          "base": "ARGUMENT:Argument"
        },
        {
          "tag": "Node",
          "attributes": {
            "name": "ARG",
            "pkg": "number",
            "type": "argNumber.py",
            "args": "$(arg negativeOne)"
          },
          "children": [],
          "metatype": "ARG",
          "base": "NODE:ARG"
        },
        {
          "tag": "Node",
          "attributes": {
            "name": "three",
            "pkg": "number",
            "type": "three.py"
          },
          "children": [],
          "metatype": "three",
          "base": "NODE:three"
        },
        {
          "tag": "Node",
          "attributes": {
            "name": "multiply",
            "pkg": "operations",
            "type": "multiply"
          },
          "children": [
            {
              "tag": "Remap",
              "attributes": {
                "from": "product",
                "to": "dividend"
              },
              "children": [],
              "metatype": "Remap",
              "base": "REMAP:->"
            }
          ],
          "metatype": "multiply",
          "base": "NODE:multiply"
        },
        {
          "tag": "Node",
          "attributes": {
            "name": "divide",
            "pkg": "operations",
            "type": "divide"
          },
          "children": [],
          "metatype": "divide",
          "base": "NODE:divide"
        },
        {
          "tag": "Remap",
          "attributes": {
            "from": "number",
            "to": "multiply1"
          },
          "children": [],
          "metatype": "Remap",
          "base": "REMAP:->"
        },
        {
          "tag": "Remap",
          "attributes": {
            "from": "three",
            "to": "multiply2"
          },
          "children": [],
          "metatype": "Remap",
          "base": "REMAP:->"
        },
        {
          "tag": "Remap",
          "attributes": {
            "from": "quotient",
            "to": "display"
          },
          "children": [],
          "metatype": "Remap",
          "base": "REMAP:->"
        },
        {
          "tag": "Include",
          "attributes": {
            "name": "display.launch"
          },
          "children": [],
          "metatype": "Include",
          "base": "INCLUDE:Include"
        },
        {
          "tag": "Group",
          "attributes": {
            "name": "denominator"
          },
          "children": [
            {
              "tag": "Node",
              "attributes": {
                "name": "four",
                "pkg": "number",
                "type": "four.py"
              },
              "children": [],
              "metatype": "four",
              "base": "NODE:four"
            },
            {
              "tag": "Node",
              "attributes": {
                "name": "two",
                "pkg": "number",
                "type": "two.py"
              },
              "children": [],
              "metatype": "two",
              "base": "NODE:two"
            },
            {
              "tag": "Node",
              "attributes": {
                "name": "add",
                "pkg": "operations",
                "type": "add"
              },
              "children": [],
              "metatype": "add",
              "base": "NODE:add"
            },
            {
              "tag": "Remap",
              "attributes": {
                "from": "four",
                "to": "add1"
              },
              "children": [],
              "metatype": "Remap",
              "base": "REMAP:->"
            },
            {
              "tag": "Remap",
              "attributes": {
                "from": "two",
                "to": "add2"
              },
              "children": [],
              "metatype": "Remap",
              "base": "REMAP:->"
            },
            {
              "tag": "Remap",
              "attributes": {
                "from": "sum",
                "to": "divisor"
              },
              "children": [],
              "metatype": "Remap",
              "base": "REMAP:->"
            }
          ],
          "base": "GROUP:Group",
          "metatype": "Group"
        }
      ]
    }

    # Ensure 'LaunchFile' type exists in the META
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
      # Create the LaunchFile node
      launch_file_node = core.create_node(params)
      # Set attributes for the new LaunchFile node
      core.set_attribute(launch_file_node, 'name', 'launch')
      logger.info(f'Created new LaunchFile node with name: "launch".')
      
      def create_child_nodes(parent_node, data):
        """
        Recursively create child nodes and their ports, handling metatype and base.
        """
        for child in data.get("children", []):
          metatype = child.get("metatype")
          base = child.get("base")
          # Ensure the metatype is valid
          if not metatype or metatype.lower() == 'null':  # Check for None or invalid "null" string
            logger.info(f"Metatype is missing or invalid for child: {child}. Defaulting to tag: {child['tag']}.")
            continue

          # Create child node
          child_node = core.create_child(parent_node, self.META[metatype])
          
          # Set the base attribute
          if base:
            core.set_attribute(child_node, "base", base)

          # Set additional attributes
          for attr, value in child.get("attributes", {}).items():
            core.set_attribute(child_node, attr, value)

          # Recursively create children
          create_child_nodes(child_node, child)

      # Start creating child nodes
      create_child_nodes(launch_file_node, launch_data)
      
      # Save changes to the project
      root_node = core.load_root(self.project.get_root_hash(self.commit_hash))
      new_commit_hash = self.util.save(root_node, self.commit_hash)
      self.project.set_branch_hash(
        branch_name=self.branch_name,
        new_hash=new_commit_hash["hash"],
        old_hash=self.commit_hash
      )
      logger.info("All nodes successfully created and saved.")
    except Exception as e:
      logger.error(f"Error during node creation: {str(e)}")
