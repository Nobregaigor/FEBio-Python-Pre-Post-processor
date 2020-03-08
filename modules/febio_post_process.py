import numpy as np
from scipy.spatial import ConvexHull
import csv
from xml.dom import minidom

from .file_manager import *
from .vector_math import *

import numpy as np
from mpl_toolkits.mplot3d import Axes3D 
import matplotlib.pyplot as plt

class FEBio_post_process():
    def __init__(self):
        self.doc = None
        self.node_sets = {}
        self.node_sets_data = {}

        self.xyz_positions = []

        self.apex_node = {}
        self.base_node = {}
        
        self.extreme_nodes = None
        self.base_params = None
        self.main_axis = None
        
        self.len_sim = 0
        

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
        self.len_sim = len(self.xyz_positions)

    def set_initial_positions(self,doc=None):
        _doc = self.doc if doc == None else doc

        nodes = {}
        data = load_by_tag(_doc, "node")
        sub_array = np.zeros(3)
        points = []
        for elem in data:
            nodes[str(elem[0])] = {"node": elem[0], "x": elem[1], "y":elem[2], "z": elem[3], "np_array": np.array([elem[1], elem[2], elem[3]])}
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
    
    def set_node_set_data(self,node_set_name,dataType,time=0):
        if len(self.node_sets_data) < 1:
            self.node_sets_data[dataType] = {}
                
        if len(self.node_sets_data[dataType]) < 1 or node_set_name not in self.node_sets_data[dataType]:
            self.node_sets_data[dataType][node_set_name] = {}
            
            
        self.node_sets_data[dataType][node_set_name][str(time)] = self.get_nodes_data_from_nodeset(node_set_name,dataType,time)
        
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
        
        main_axis = {}
        if apex_node_idx == 0 or 3:
            main_axis['x'] = 0
        elif apex_node_idx == 1 or 4:
            main_axis['y'] = 1
        else:
            main_axis['z'] = 2
            
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
        center_x = sum_x * 0.25
        center_y = sum_y * 0.25
        center_z = sum_z * 0.25
        
        base_node = {
            'node': "REF:BASE",
            'x': center_x,
            'y': center_y,
            'z': center_z,
            "np_array": np.array([center_x, center_y, center_z])
        }
        
        vectors_from_base = []
        for node in extreme_nodes:
            vec = np.subtract(node["np_array"], base_node["np_array"])
            vectors_from_base.append(vec)
        
        base_params = {
            "vectors_from_base": vectors_from_base,
            "nomarl": np.cross(vectors_from_base[0], vectors_from_base[1]),
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
            self.base_params = base_params
            self.main_axis = main_axis
        else:
            return {
                "apex_node": apex_node,
                "base_node": base_node,
                "extreme_nodes": extreme_nodes,
                "base_params": base_params,
                "main_axis": main_axis
                }
    
    def get_closest_node(self,node_ref_id,node_set=None,time=0,axis=None):
        if node_set == None:
            nodes = self.xyz_positions[time]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz',time=time)
            elif type(node_set) == dict:
                nodes = node_set
            else:
                raise(ValueError("get_closest_node: node_set type not understood"))
        
        node_ref_id = str(node_ref_id)
        if node_ref_id in nodes:
            node_ref = nodes[node_ref_id]
            inter_nodes = iter(nodes)
            next_node_id = next(inter_nodes)
            if next_node_id == node_ref_id:
                next_node_id = next(inter_nodes)
            node = nodes[next_node_id]
            if axis == None:
                dist = self.get_xyz_distance(node_ref,node)
            else:
                dist = abs(node_ref[axis] - node[axis])
            close_node = node
            for node_id in nodes:
                if node_id != node_ref_id:
                    node = nodes[node_id]
                    if axis == None:
                        new_dist = self.get_xyz_distance(node_ref,node)
                    else:
                        new_dist = abs(node_ref[axis] - node[axis])
                    if new_dist < dist:
                        dist = new_dist
                        close_node = node
            return close_node, dist
        else:
            raise(ValueError("get_closest_node: node_ref_id not in nodes"))
    
    def get_farthest_node(self,node_ref_id,node_set=None,time=0,axis=None):
        if node_set == None:
            nodes = self.xyz_positions[time]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz',time=time)
            elif type(node_set) == dict:
                nodes = node_set
            else:
                raise(ValueError("get_farthest_node: node_set type not understood"))
        
        node_ref_id = str(node_ref_id)
        if node_ref_id in nodes:
            node_ref = nodes[node_ref_id]
            inter_nodes = iter(nodes)
            next_node_id = next(inter_nodes)
            if next_node_id == node_ref_id:
                next_node_id = next(inter_nodes)
            node = nodes[next_node_id]
            if axis == None:
                dist = self.get_xyz_distance(node_ref,node)
            else:
                dist = abs(node_ref[axis] - node[axis])
            far_node = node
            for node_id in nodes:
                if node_id != node_ref_id:
                    node = nodes[node_id]
                    if axis == None:
                        new_dist = self.get_xyz_distance(node_ref,node)
                    else:
                        new_dist = abs(node_ref[axis] - node[axis])
                    if new_dist > dist:
                        dist = new_dist
                        far_node = node
            return far_node, dist
        else:
            raise(ValueError("get_farthest_node: node_ref_id not in nodes"))
        
    def get_nodes_within_range(self,node_ref_id,dist=None,al_err=0.1,node_set=None,time=0):
        if node_set == None:
            nodes = self.xyz_positions[time]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz',time=time)
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
        
        max_tries = 25
        trial_idx = 0
        
        while len(nodes_within_range) < 5:
            if trial_idx > max_tries:
                print("Warning: Max number of trials reached when trying to find nodes within range.\n")
                return nodes_within_range
            
            for node_id in nodes:
                if node_id != node_ref_id:
                    node = nodes[node_id]
                    new_dist = self.get_xyz_distance(node_ref,node)
                    if min_dist < new_dist < max_dist:
                        nodes_within_range[node_id] = node
            
            al_err += 0.05
            
            min_dist = dist * (1 - al_err)
            max_dist = dist * (1 + al_err)
            
            trial_idx += 1
            
        return nodes_within_range       
    
    def get_nodes_along_dir(self,dir_vec, node_ref_id=None, al_err=0.001, node_set=None, time=0):
        if node_set == None:
            nodes = self.xyz_positions[time]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz',time=time)
            elif type(node_set) == dict:
                nodes = node_set
            else:
                raise(ValueError("get_nodes_along_dir: node_set type not understood"))
        
        nodes_along_dir = {}
        
        max_tries = 25
        trial_idx = 0
        
        if node_ref_id == None:
            if len(self.base_node) > 0:
                node_ref = self.base_node
            else:
                node_ref = {"np_array": np.array([0,0,0])}
        else:
            if node_ref_id == "REF:BASE":
                if len(self.base_node) > 0:
                    node_ref = self.base_node
                else:
                    raise(ValueError("get_nodes_along_dir: self.base_node not defined."))
            elif node_ref_id in nodes:
                node_ref = nodes[node_ref_id]
            else:
                raise(ValueError("get_nodes_along_dir: node_ref_id not in nodes."))
        
        while len(nodes_along_dir) < 1:
            if trial_idx > max_tries:
                print("Warning: Max number of trials reached when trying to find nodes along dir.\n")
                return nodes_along_dir
        
            for node_id in nodes:
                node = nodes[node_id]
                node_dir = np.subtract(node["np_array"],node_ref["np_array"])
                angle = angle_between(dir_vec, node_dir)
                if -al_err < angle < al_err:
                    nodes_along_dir[node_id] = node
            al_err += 0.01
            trial_idx += 1
            
        return nodes_along_dir
    
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

    def cal_radius(self,node_set=None,time=0):
        if len(self.base_node) < 1:
            print("get_radius: self.base_node is not defined. Please, use get_apex_and_base_nodes method.")
            raise
        elif len(self.base_params) < 1:
            print("get_radius: self.base_params is not defined. Please, use get_apex_and_base_nodes method.")
            raise
        else:
            if node_set == None:
                nodes = self.xyz_positions[time]["nodes"]
            else:
                if type(node_set) == str:
                    nodes = self.get_nodes_data_from_nodeset(node_set,'xyz',time=time)
                elif type(node_set) == dict:
                    nodes = node_set
                else:
                    raise(ValueError("get_radius: node_set type not understood"))
                
            node_ref = self.base_node
            
            nodes_along_radius = []
            mean_dist = 0
            n_means = 0
            for dir_vec in self.base_params["vectors_from_base"]:
                nodes_along_dir = self.get_nodes_along_dir(dir_vec,node_ref_id=node_ref["node"],node_set=nodes,time=time)
                dist = 0
                n_dist = 0
                for nodes_along_dir_ids in nodes_along_dir:
                    node_ = nodes_along_dir[nodes_along_dir_ids]
                    dist += self.get_xyz_distance(node_ref, node_)
                    n_dist += 1
                mean_dist += dist / n_dist
                n_means += 1
                nodes_along_radius.append(nodes_along_dir)
            
            mean_dist = mean_dist / n_means
            
            
            return mean_dist, nodes_along_radius
    
    ##################################################
    # Post-Process Methods
    ##################################################

    def ejection_fraction(self,endocardio_node_set_name="Endocardio"):
        # Calculting volume (inital and final)
        v_0 = self.cal_vol(0,endocardio_node_set_name)
        v_1 = self.cal_vol(self.len_sim-1,endocardio_node_set_name)
        
        # Converting to ml
        v_0 = v_0 * 0.001
        v_1 = v_1 * 0.001
        
        print("         -> initial volume (ml) = ", v_0)
        print("         -> final volume (ml) = ", v_1)

        return abs((v_0 - v_1) / v_0)

    def thickness_fraction(self,endo_node_set_name="Endocardio",epi_node_set_name="Epicardio"):
        
        # Poiting to node_sets_data 
        # Initial state
        i_endo_node_set_data = self.node_sets_data["position"][endo_node_set_name]['0']
        i_epi_node_set_data = self.node_sets_data["position"][epi_node_set_name]['0']
        # Final state
        f_endo_node_set_data = self.node_sets_data["position"][endo_node_set_name][str(self.len_sim-1)]
        f_epi_node_set_data = self.node_sets_data["position"][epi_node_set_name][str(self.len_sim-1)]
        
        # Calculating radius
        # Initial state
        i_endo_radius = self.cal_radius(node_set=i_endo_node_set_data)[0]
        i_epi_radius = self.cal_radius(node_set=i_epi_node_set_data)[0]
        print("         -> initial endo radius = ", i_endo_radius)
        print("         -> initial epi radius = ", i_epi_radius)
        # Final state
        f_endo_radius = self.cal_radius(node_set=f_endo_node_set_data)[0]
        f_epi_radius = self.cal_radius(node_set=f_epi_node_set_data)[0]
        print("         -> final endo radius = ", f_endo_radius)
        print("         -> final epi radius = ", f_epi_radius)
        
        # Calculating wall thickness
        i_wall_th = i_epi_radius - i_endo_radius
        f_wall_th = f_epi_radius - f_endo_radius
        print("         -> initial wall thi = ", i_wall_th)
        print("         -> final wall thi = ", f_wall_th)
        
        # Calculating Thickness fraction
        th_frac = (f_wall_th - i_wall_th) / i_wall_th
        
        return th_frac, [i_wall_th, f_wall_th]
    
    def apex_thickness_fraction(self,endo_node_set_name="Endocardio"):
        
        apex_node_id = self.apex_node["node"]
        i_epi_apex = nodes = self.xyz_positions[0]["nodes"][str(apex_node_id)]
        f_epi_apex = nodes = self.xyz_positions[self.len_sim-1]["nodes"][str(apex_node_id)]
        
        i_endo_apex = self.get_apex_and_base_nodes(self.node_sets_data["position"][endo_node_set_name]['0'], set_as_properties=False)
        f_endo_apex = self.get_apex_and_base_nodes(self.node_sets_data["position"][endo_node_set_name][str(self.len_sim-1)], set_as_properties=False)
        i_endo_apex = i_endo_apex["apex_node"]
        f_endo_apex = f_endo_apex["apex_node"]
        
        i_apex_wall_th = self.get_xyz_distance(i_endo_apex,i_epi_apex)
        f_apex_wall_th = self.get_xyz_distance(f_endo_apex,f_epi_apex)
        
        print("             -> initial apex wall thickness = ", i_apex_wall_th)
        print("             -> final apex wall thickness = ", f_apex_wall_th)
        
        return (f_apex_wall_th - i_apex_wall_th) / i_apex_wall_th
    
    def radial_shortening(self, endo_node_set_name="Endocardio"):
        
        i_endo_node_set_data = self.node_sets_data["position"][endo_node_set_name]['0']
        f_endo_node_set_data = self.node_sets_data["position"][endo_node_set_name][str(self.len_sim-1)]
        
        i_endo_radius = self.cal_radius(node_set=i_endo_node_set_data)[0]
        f_endo_radius = self.cal_radius(node_set=f_endo_node_set_data)[0]
        
        print("         -> initial endo radius = ", i_endo_radius)
        print("         -> final endo radius = ", f_endo_radius)
        
        return (f_endo_radius - i_endo_radius) / i_endo_radius


    def plot_surface(self,node_set=None,time=0):
        if node_set == None:
            nodes = self.xyz_positions[time]["nodes"]
        else:
            if type(node_set) == str:
                nodes = self.get_nodes_data_from_nodeset(node_set,'xyz',time=time)
            elif type(node_set) == dict:
                nodes = node_set
            else:
                raise(ValueError("get_nodes_along_dir: node_set type not understood"))

        # print("nodes",nodes)

        x = np.zeros(len(nodes))
        y = np.zeros(len(nodes))
        z = np.zeros(len(nodes))
        
        idx = 0
        for key in nodes:
            elem = nodes[key]
            # print(elem)
            x[idx] = elem["x"]
            y[idx] = elem["y"]
            z[idx] = elem["z"]

            idx += 1
            
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        ax.scatter(x, y, z)

        ax.set_xlabel(' X ')
        ax.set_ylabel(' Y ')
        ax.set_zlabel(' Z ')

        plt.show()
        
        
        
        