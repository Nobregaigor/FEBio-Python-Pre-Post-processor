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

        self.apex_node = {}
        self.base_node = {}

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
        """ Hello """
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
    
    def get_nodes_data_from_nodeset(self,node_set_name,dataType,time=0):
        if node_set_name in self.node_sets:
            dataType = dataType.lower()
            output = {}
            if dataType == "xyz" or "position" or "positions":
                data = self.xyz_positions[time]['nodes']
                for node_id in self.node_sets[node_set_name]:
                    output[str(node_id)] = data[str(node_id)]
                return output
            else:
                raise(ValueError("get_nodes_data_from_nodeset: dataType not understood or was not implemented"))
        else:
            raise(ValueError("get_nodes_data_from_nodeset: node_set_name not defined in self.node_sets"))

    def get_xyz_distance(self,node_1,node_2):
        delta_x = node_1['x'] - node_2['x']
        delta_y = node_1['y'] - node_2['y']
        delta_z = node_1['z'] - node_2['z']
        
        return np.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
    
    def get_apex_and_base_nodes(self,node_set=None,set_as_properties=False):
        if node_set == None:
            nodes = self.xyz_positions[0]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz')
            elif type(node_set) == dict:
                nodes = node_set
            else:
                raise(ValueError("get_closest_node: node_set type not understood"))

        def get_min_max(direction, prev_min, prev_max, new):
            min_val = new if new[direction] < prev_min[direction] else prev_min
            max_val = new if new[direction] > prev_max[direction] else prev_max

            return min_val, max_val
            

        # Get min and max nodes from all coordinates
        first_key = next(iter(nodes))
        min_x, max_x = get_min_max('x', nodes[first_key], nodes[first_key], nodes[first_key])
        min_y, max_y = get_min_max('y', nodes[first_key], nodes[first_key], nodes[first_key])
        min_z, max_z = get_min_max('z', nodes[first_key], nodes[first_key], nodes[first_key])

        for node_id in nodes:
            node = nodes[node_id]
            min_x, max_x = get_min_max('x', min_x, max_x, node)
            min_y, max_y = get_min_max('y', min_y, max_y, node)
            min_z, max_z = get_min_max('z', min_z, max_z, node)

        # Create an array of min and max nodes (extremes of the mesh)
        extreme_nodes = [min_x, min_y, min_z, max_x, max_y, max_z]
        
        # Set an initial value to keep track of mean distance (between each node)
        mean_dist = 0
        
        # Loop through all nodes and calculate the distance with respect to the other nodes
        for i in range(0,6):
            
            # Set an initial value to sum and calculate the mean of the distances
            distance_sum = 0
            # Point to node to be analized       
            node_1 = extreme_nodes[i]
            # sum the straight line from node_1 to all other nodes (defined as node_2)
            for j in range(0,6):
                if j != i:
                    node_2 = extreme_nodes[j]
                    distance_sum += self.get_xyz_distance(node_1,node_2)
            
            # Calculate the mean distances
            new_mean_dist = distance_sum * 0.2
            
            # Check if the new mean is larger to the previous mean
            if new_mean_dist >= mean_dist:
                # Set the new mean as the curr mean
                mean_dist = new_mean_dist
                # Point to appex node and set the node idx (that will be removed from extremes later)
                apex_node = node_1
                apex_node_idx = i 
        
        # Get the idx of the opposite node of apex (won't be used to calculate the centroid)
        node_opposite_to_apex = apex_node_idx + 2 if apex_node_idx < 3 else apex_node_idx - 3

        # Delete the apex node and opposite node from the extreme nodes (already found the apex)
        del extreme_nodes[apex_node_idx]
        del extreme_nodes[node_opposite_to_apex]
        
        # Find centroid between remaining nodes (where base node will be located)
        sum_x = 0
        sum_y = 0
        sum_z = 0
        for node in extreme_nodes:
            sum_x += node['x']
            sum_y += node['y']
            sum_z += node['z']
        
        # Create an object to be set as the base_node
        base_node = {
            'node': "REF",
            'x': sum_x * 0.25,
            'y': sum_y * 0.25,
            'z': sum_z * 0.25,
        }
        
        # Point to mins and maxs (for later reference, if needed)
        mins = {'x': min_x, 'y': min_y, 'z': min_z}
        maxs = {'x': max_x, 'y': max_y, 'z': max_z}
        extreme_nodes = {'min': mins, 'max': maxs}
        
        # Set class properties to define apex and base nodes if set_as_properties is enabled
        if set_as_properties:
            self.apex_node = apex_node
            self.base_node = base_node
            self.extreme_nodes = extreme_nodes
        else:
            return {
                "apex_node": apex_node,
                "base_node": base_node,
                "extreme_nodes": extreme_nodes
                }
    
    def get_closest_node(self,node_ref_id,node_set=None):
        if node_set == None:
            nodes = self.xyz_positions[0]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz')
            elif type(node_set) == dict:
                nodes = node_set
            else:
                raise(ValueError("get_closest_node: node_set type not understood"))
        
        node_ref_id = str(node_ref_id)
        if node_ref_id in nodes:
            node_ref = nodes[node_ref_id]
            node = nodes[next(iter(nodes))]
            dist = self.get_xyz_distance(node_ref,node)
            close_node = node
            for node_id in nodes:
                if node_id != node_ref_id:
                    node = nodes[node_id]
                    new_dist = self.get_xyz_distance(node_ref,node)
                    if new_dist < dist:
                        dist = new_dist
                        close_node = node
            return close_node, dist
        else:
            raise(ValueError("get_closest_node: node_ref_id not in nodes"))
    
    def get_nodes_within_range(self,node_ref_id,dist=None,al_err=0.1,node_set=None):
        if node_set == None:
            nodes = self.xyz_positions[0]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz')
            elif type(node_set) == dict:
                nodes = node_set
            else:
                raise(ValueError("get_closest_node: node_set type not understood"))
            
        node_ref_id = str(node_ref_id)
        
        if dist == None: #Default: closest distance
            closest_node, dist = self.get_closest_node(node_ref_id,node_set=nodes)
        
        min_dist = dist * (1 - al_err)
        max_dist = dist * (1 + al_err)
        
        nodes_within_range = {}
        node_ref = nodes[node_ref_id]
        
        max_tries = 10
        trial_idx = 0
        
        while len(nodes_within_range) < 5:
            if trial_idx > max_tries:
                print("Max number of trials reached, please, increase allowed error.")
                raise
            
            for node_id in nodes:
                if node_id != node_ref_id:
                    node = nodes[node_id]
                    new_dist = self.get_xyz_distance(node_ref,node)
                    if min_dist < new_dist < max_dist:
                        nodes_within_range[node_id] = node
            
            al_err += 0.025
            
            min_dist = dist * (1 - al_err)
            max_dist = dist * (1 + al_err)
            
            trial_idx += 1
            
        return nodes_within_range       
    

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
