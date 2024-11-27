"""
This is where the implementation of the plugin code goes.
The ExportLaunch-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('ExportLaunch')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class ExportLaunch(PluginBase,indent=0):
    def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        
        visited_nodes = []
        ignoreMetaType = ["GroupPublisher","GroupSubscriber","Subscriber","Topic","Publisher"]
        nodeLibrary = []
        def xmlGenerator(activeNode,indent = 0,topLevel = True):
            
            result = ""
            node_path = core.get_path(activeNode)
            
            if topLevel:
                result += " " * indent + "\n<launch>\n"
                
            if node_path in visited_nodes:
                #logger.warning(f"Node already visited, skipping: {node_path}")
                return result +'\n</launch>'
            
            visited_nodes.append(node_path)
            children = core.load_children(activeNode)
            
            for child in children:
                
                meta_type = core.get_meta_type(child)
                metaTypeName = core.get_attribute(meta_type,'name')
                childName = core.get_attribute(child,'name')
                logger.info(f"metaTypeName {metaTypeName}")
                
                if metaTypeName in ignoreMetaType:
                    continue
                #logger.info(f"{core.get_attribute(child, 'pkg')} {core.get_attribute(child, 'type')} {core.get_attribute(child, 'args')} {core.get_attribute(child, 'name')} core.get_attribute(child, 'args')")
                if metaTypeName == "Argument":
                    arg_name = core.get_attribute(child, 'name')
                    arg_value = core.get_attribute(child, 'value')
                    logger.info(f"{arg_name} {arg_value}")
                    result += f"{' ' * (indent + 2)}<arg name=\"{arg_name}\" value=\"{arg_value}\"/>\n"
                    #result += f"{' ' * indent}{childName}()\n"
                
                elif core.get_attribute(child, 'pkg') or core.get_attribute(child, 'type') or core.get_attribute(child, 'args') or core.get_attribute(child, 'respawn'):
                    #pkg = "operations"
                    result += f"{' ' * (indent + 2)}<node name=\"{childName}\" pkg=\"{core.get_attribute(child, 'pkg')}\" type=\"{metaTypeName}\" args=\"{ core.get_attribute(child, 'args')}\">\n"
                    result += xmlGenerator(child, indent + 4,topLevel = False)
                    result += f"{' ' * (indent + 2)}</node>\n"

                elif metaTypeName == "Remap":
                    remap_from = core.get_attribute(child, 'from')
                    remap_to = core.get_attribute(child, 'to')
                    result += f"{' ' * (indent + 2)}<remap from=\"{remap_from}\" to=\"{remap_to}\"/>\n"    
                
                elif metaTypeName == "Include":
                    file_name = core.get_attribute(child, 'name')
                    if '.launch' not in file_name:
                        logger.info(f"{file_name}")
                        result += f"{' ' * (indent + 2)}<include file=\"{file_name}.launch\"/>\n"
                    else:
                        result += f"{' ' * (indent + 2)}<include file=\"{file_name}\"/>\n"
                
                elif metaTypeName == "Group":
                    ns = core.get_attribute(child, 'name')
                    result += f"{' ' * (indent + 2)}<group ns=\"{ns}\">\n"
                    # Recursively process children of the group
                    result += xmlGenerator(child, indent + 4,topLevel = False)
                    result += f"{' ' * (indent + 2)}</group>\n"
                
            if topLevel:
                result += " " * indent + "</launch>\n"
            return result
        output = xmlGenerator(active_node)
        logger.info(f"output {output}")
        file_name = 'output.xml'
        file_hash = self.add_file(file_name, output)
        logger.info(f"Output saved to file with hash: {file_hash}")

