import numpy as np
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

        convex_hull = sp_spl.ConvexHull(points)

        return convex_hull.volume

    def ejection_fraction(self,endocardio_node_set_name="Endocardio"):
        v_0 = self.cal_vol(0,endocardio_node_set_name)
        v_1 = self.cal_vol(len(self.xyz_positions),endocardio_node_set_name)

        v_0 = v_0 * 0.001
        v_1 = v_1 * 0.001

        return (v_0 - v_1) / v_0
