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
    print("#"*60)
    print("Initializing Post Process:")
    # Storing the Post process at location defined by myo_post_process
    myo_post_process = FEBio_post_process()
    # Creating a doc for the desired post process file
    myo_post_process.create_doc(myo_feb_file_path)
    
    # Adding NodeSets to the object
    print("     Adding node sets...")
    myo_post_process.add_node_set("Epicardio")
    myo_post_process.add_node_set("Endocardio")
    myo_post_process.add_node_set("Top_surface")
    
    # Set inital positions obtained by .feb model
    print("     Setting positions...")
    myo_post_process.set_initial_positions()
    # Set positions obtained by the simulations
    myo_post_process.set_sim_positions(position_nodes_out_file_path)
    
    # Set position data attributed to each data_set (makes run faster since many functions require the data from a node_set)
    print("     Setting node set data (position)...")
    myo_post_process.set_node_set_data("Epicardio","position",0)
    myo_post_process.set_node_set_data("Endocardio","position",0)
    myo_post_process.set_node_set_data("Epicardio","position",myo_post_process.len_sim-1)
    myo_post_process.set_node_set_data("Endocardio","position",myo_post_process.len_sim-1)
    
    # Get Apex and base node. Base node will be a REF node, since it is not contained in mesh
    print("     Getting apex and base from nodes position data...")
    myo_post_process.get_apex_and_base_nodes(set_as_properties=True)
    
    # ___________________
    # Calculations
    # ___________________
    print("\n" + "#"*60)
    print("Performing Calculations:")
    
    # Calculating Ejection Fraction
    print("     Calculating Ejection Fraction...")
    ejection_fraction = myo_post_process.ejection_fraction()
    
    print("     Calculating Wall Thickness Fraction...")
    wall_th_frac = myo_post_process.thickness_fraction()[0]
    
    print(" Calculating Apex Wall Thickness Fraction...")
    apex_wall_th_frac = myo_post_process.apex_thickness_fraction()
    
    print(" Calculating Radial Shortening...")
    radial_shortening = myo_post_process.radial_shortening()
    
    # ___________________
    # Printing / saving results
    # ___________________
    print("\n" + "#"*60)
    print("Results:\n")
    
    print("     Ejection Fraction            = ", ejection_fraction)
    print("     Wall Thickness Fraction      = ", wall_th_frac)
    print("     Apex Wall Thickness Fraction = ", apex_wall_th_frac)
    print("     Radial Shortening            = ", apex_wall_th_frac)
    
    # print(ejection_fraction)
    # print("hello")
    
