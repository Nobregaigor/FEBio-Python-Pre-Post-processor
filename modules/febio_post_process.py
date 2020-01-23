import scipy.spatial as sp_spl
import csv

from xml.dom import minidom

from .file_manager import *

class FEBio_post_process():
    def __init__(self):
        self.doc = None
        self.node_sets = {}
        
        self.xyz_positions = []
                    
    def create_doc(self,file_path):
        self.doc = minidom.parse(file_path)
        
    def add_node_set(self,node_set_name, doc=None):
        _doc = self.doc if doc == None else doc
        self.node_sets[node_set_name] = get_nodes_from_nodeset(_doc, node_set_name)
        
    def set_sim_positions(self,positions_file_path):
        self.xyz_positions = read_feb_out_txt_file(positions_file_path)
        
    def set_initial_positions(self,doc=None):
        _doc = self.doc if doc == None else doc
        
        nodes = {}
        data = load_by_tag(_doc, "node")
        for elem in data:
            nodes[str(elem[0])] = {"node": elem[0], "x": elem[1], "y":elem[2], "z": elem[3]}
        
        output = {
                "step": 0,
                "time": 0,
                "struct": ['x','y','z'],
                "nodes": nodes,
                "val": None
            }
        return output
            
    