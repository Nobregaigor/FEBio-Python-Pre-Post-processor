from modules import *
from pprint import pprint as pp

import numpy as np

if __name__ == "__main__":

    # ___________________
    # File Paths
    # ___________________
    myo_feb_file_path = "input/LinearConstrainTest3_1.feb"
    position_nodes_out_file_path = "input/simulation_outputs/position_node_out.txt"

    # ___________________
    # Creating Object for Post Process
    # ___________________
    print("Initializing Post Process...")
    # Storing the Post process at location defined by myo_post_process
    myo_post_process = FEBio_post_process()
    # Creating a doc for the desired post process file
    myo_post_process.create_doc(myo_feb_file_path)
    # Adding NodeSets to the object
    myo_post_process.add_node_set("Epicardio")
    myo_post_process.add_node_set("Endocardio")
    myo_post_process.add_node_set("Top_surface")
    # Set inital positions obtained by .feb model
    myo_post_process.set_initial_positions()
    # Set positions obtained by the simulations
    myo_post_process.set_sim_positions(position_nodes_out_file_path)
    # Get Apex and base node. Base node will be a REF node, since it is not contained in mesh
    myo_post_process.get_apex_and_base_nodes(set_as_properties=True)
    
    # apex = myo_post_process.apex_node
    # nodes_within_range = myo_post_process.get_nodes_along_dir(np.array([0,0,1]))
    # print(nodes_within_range[0])
    
    radius_nodes, radius = myo_post_process.get_radius(node_set="Endocardio",time=1)
    print(radius)
    
    
    
    # inner_r_0 = get_inner_radius()
    

    # ___________________
    # Calculations
    # ___________________
    print("Performing Calculations...")
    # Calculating Ejection Fraction
    ejection_fraction = myo_post_process.ejection_fraction()
    # print(ejection_fraction)
    # print("hello")
    
