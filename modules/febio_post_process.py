import numpy as np
from scipy.spatial import ConvexHull
import csv
from xml.dom import minidom

from .file_manager import *

class FEBio_post_process():
    def __init__(self):
        self.doc = None
        self.node_sets = {}

        self.xyz_positions = []
        
        self.apex_nodes = {}
        self.base_nodes = {}
        
    ##################################################
    # Fundamental Methods
    ##################################################

    def create_doc(self,file_path):
        self.doc = minidom.parse(file_path)

    def add_node_set(self,node_set_name, doc=None):
        _doc = self.doc if doc == None else doc
        self.node_sets[node_set_name] = get_nodes_from_nodeset(_doc, node_set_name)

    def set_sim_positions(self,positions_file_path):
        self.xyz_positions.extend(read_feb_out_txt_file(positions_file_path))

    def set_initial_positions(self,doc=None):
        _doc = self.doc if doc == None else doc

        nodes = {}
        data = load_by_tag(_doc, "node")
        sub_array = np.zeros(3)
        points = []
        for elem in data:
            nodes[str(elem[0])] = {"node": elem[0], "x": elem[1], "y":elem[2], "z": elem[3]}
            sub_array[0] = elem[1]
            sub_array[1] = elem[1]
            sub_array[2] = elem[2]
            points.append(sub_array)
            
        output = {
                "step": 0,
                "time": 0,
                "struct": ['x','y','z'],
                "nodes": nodes,
                "val": None,
                "points": points,
            }
        
        self.xyz_positions.append(output)
        
    ##################################################
    # Aditional Parameters Methods
    ##################################################
    
    def get_apex_and_base_nodes(self):
        nodes = self.xyz_positions[0]["nodes"]
        
        def get_min_max(direction, prev_min, prev_max, new):
            min_val = new if new[direction] < prev_min[direction] else prev_min
            max_val = new if new[direction] > prev_max[direction] else prev_max
            
            return min_val, max_val
        
        def is_within_range(direction,param,node, error):
            if param[direction] - error < node[direction] < param[direction] + error:
                return True
            else:
                return False
            
        min_x, max_x = get_min_max('x', nodes["1"], nodes["1"], nodes["1"])
        min_y, max_y = get_min_max('y', nodes["1"], nodes["1"], nodes["1"])
        min_z, max_z = get_min_max('z', nodes["1"], nodes["1"], nodes["1"])
                        
        for node_id in nodes:
            node = nodes[node_id]
            min_x, max_x = get_min_max('x', min_x, max_x, node)
            min_y, max_y = get_min_max('y', min_y, max_y, node)
            min_z, max_z = get_min_max('z', min_z, max_z, node)
            
        mins = {'x': min_x, 'y': min_y, 'z': min_z}
        maxs = {'x': max_x, 'y': max_y, 'z': max_z}
        
        self.apex_nodes = mins
        self.base_nodes = maxs
        
        # for node_id in nodes:
        #     node = nodes[node_id]
        #     count_min_x = count_x + 1 if is_within_range('x', min_x,node,5)
        #     count_min_y = count_x + 1 if is_within_range('y', min_y,node,5)
        #     count_min_z = count_x + 1 if is_within_range('z', min_z,node,5)
              
    
    
    ##################################################
    # Calculation Methods
    ##################################################

    def cal_vol(self,position,node_set=None):
        if node_set != None:
            data = self.xyz_positions[position]
            n_nodes = len(self.node_sets[node_set])
            points = np.zeros(n_nodes,dtype=np.dtype((np.dtype('f8'), (3))))
            i = 0
            for id in self.node_sets[node_set]:
                node = data["nodes"][str(id)]
                points[i] = np.array([node["x"], node["y"], node["z"]])
                i += 1
        else:
            points = self.xyz_positions[position]["points"]

        convex_hull = ConvexHull(points)

        return convex_hull.volume
    
    ##################################################
    # Post-Process Methods
    ##################################################

    def ejection_fraction(self,endocardio_node_set_name="Endocardio"):
        v_0 = self.cal_vol(0,endocardio_node_set_name)
        v_1 = self.cal_vol(len(self.xyz_positions)-1,endocardio_node_set_name)

        v_0 = v_0 * 0.001
        v_1 = v_1 * 0.001

        return abs((v_0 - v_1) / v_0)
    


