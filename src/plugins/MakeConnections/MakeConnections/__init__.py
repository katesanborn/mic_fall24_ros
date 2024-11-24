"""
This is where the implementation of the plugin code goes.
The MakeConnections-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('MakeConnections')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class MakeConnections(PluginBase):
    def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        
        publishers = []
        subscribers = []
        topics = []
        remaps = []
        
        def at_node(node):
            meta_node = core.get_base_type(node)
            name = core.get_attribute(node, 'name')
            path = core.get_path(node)
            meta_type = 'undefined'
            if meta_node:
                meta_type = core.get_attribute(meta_node, 'name')
            if meta_type == "Publisher":
                publishers.append(node)
            if meta_type == "Subscriber":
                subscribers.append(node)
            if meta_type == "Topic":
                topics.append(node)
            if meta_type == "Remap":
                remaps.append(node)
            
        def get_connectable_ports(node):
            pubs = []
            subs = []
            
            children = core.load_children(node)
            for c in children:
                grand_children = core.load_children(c)
                for g in grand_children:
                    meta_node = core.get_base_type(g)
                    meta_type = core.get_attribute(meta_node, 'name')
                    if meta_type == "Publisher":
                        pubs.append(g)
                    if meta_type == "Subscriber":
                        subs.append(g)
                    
            return (pubs, subs)
        
        
        def draw_connection(pub, sub, name):
            parent = core.get_common_parent([pub, sub])
            
            new_topic = core.create_child(parent, self.util.META(active_node)["Topic"])
            
            core.set_pointer(new_topic, 'src', pub)
            core.set_pointer(new_topic, 'dst', sub)
            core.set_attribute(new_topic, 'name', name)
            
        # Get list of publishers, subscribers, and topics    
        self.util.traverse(active_node, at_node)
        
        # Delete all existing topics connections
        for t in topics:
            core.delete_node(t)
        
        # Set up empty dictionary for pubs and subs
        pub_dict = dict()
        sub_dict = dict()
        
        # Set up publisher and subscriber dictionary before remap
        for p in publishers:
            name = core.get_attribute(p, 'name')
            pub_dict[p["nodePath"]] = {"old_name": name, "remap_name": name}
            
        for s in subscribers:
            name = core.get_attribute(s, 'name')
            sub_dict[s["nodePath"]] = {"old_name": name, "remap_name": name}
            
        def count_slashes(string):
            return string["nodePath"].count('/')
        
        # Apply remaps in correct order
        sorted_remaps = sorted(remaps, key=count_slashes)
        for r in reversed(sorted_remaps):
            r_parent = core.get_parent(r)

            r_from = core.get_attribute(r, 'from')
            r_to = core.get_attribute(r, 'to')
        
            def remap_fcn(node):
                meta_node = core.get_base_type(node)
                meta_type = core.get_attribute(meta_node, 'name')
                if meta_type == "Publisher" or meta_type == "Subscriber":
                    if node["nodePath"] in pub_dict:
                        if pub_dict[node["nodePath"]]["remap_name"] == r_from:
                            pub_dict[node["nodePath"]]["remap_name"] = r_to
                    if node["nodePath"] in sub_dict:
                        if sub_dict[node["nodePath"]]["remap_name"] == r_from:
                            sub_dict[node["nodePath"]]["remap_name"] = r_to
            
            children = core.load_children(r_parent)
            for c in children:
                self.util.traverse(c, remap_fcn)
        
        logger.info(pub_dict)
        logger.info(sub_dict)
        
        # Draw new topic connections
        def connect_at_node(node):
            meta_node = core.get_base_type(node)
            meta_type = core.get_attribute(meta_node, 'name')
            if not(meta_type == "LaunchFile" or meta_type == "Group"):
                return
        
            pubs, subs = get_connectable_ports(node)
        
            for p in pubs:
                for s in subs:
                    p_topic = pub_dict[p["nodePath"]]["remap_name"]
                    s_topic = sub_dict[s["nodePath"]]["remap_name"]
                
                    if p_topic == s_topic:
                        draw_connection(p, s, p_topic)
        
        self.util.traverse(active_node, connect_at_node)
        
        # Save updates
        new_commit_hash = self.util.save(core.load_root(self.project.get_root_hash(self.commit_hash)), self.commit_hash)    
        self.project.set_branch_hash(
            branch_name=self.branch_name,
            new_hash=new_commit_hash["hash"],
            old_hash=self.commit_hash
        )
        
        logger.info("DONE")
