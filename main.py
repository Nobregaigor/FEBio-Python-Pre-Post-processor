from modules import *
from pprint import pprint as pp
import numpy as np

import sys, getopt
from pathlib import Path
from os import listdir
from os.path import isfile, join

def get_input_arguments(argv):
    i_folder = None
    o_folder = None
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifolder=","ofolder="])
    except getopt.GetoptError:
        print('Error in command input. Format should be: -i <inputfolder> -o <outputfolder>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('-i <inputfolder> -o <outputfolder>')
            sys.exit()
        elif opt in ("-i", "--ifolder"):
            i_folder = arg
        elif opt in ("-o", "--ofolder"):
            o_folder = arg

    if o_folder == None:
        o_folder = i_folder # default value

    if i_folder == None:
        print("Error: no input folder.")
        sys.exit(-1)

    return i_folder, o_folder


if __name__ == "__main__":
    i_folder, o_folder = get_input_arguments(sys.argv[1:])
    
    files = [f for f in listdir(i_folder) if isfile(join(i_folder, f))]
    
    for file in files:
        if file.rfind(".feb") != -1:
            myo_feb_file_path = join(i_folder,file)
        elif file.find("position_node_out") != -1:
            position_nodes_out_file_path = join(i_folder,file)

    if myo_feb_file_path == None or position_nodes_out_file_path == None:
        print("Error: check files in input folder. Did not find .feb or 'position_node_out'")
        sys.exit(-1)
    
    # ___________________
    # File Paths
    # ___________________
    # myo_feb_file_path = "input/Myo_ideal_tet_unv_2_with_fibers.feb"
    # position_nodes_out_file_path = "input/active_sim_outputs/position_node_out.txt"

    # ___________________
    # Creating Object for Post Process
    # ___________________
    print("#"*60)
    print("Initializing Post Process:")
    # Storing the Post process at location defined by m_p_p
    m_p_p = FEBio_post_process()
    # Creating a doc for the desired post process file
    m_p_p.create_doc(myo_feb_file_path)
    
    # Adding NodeSets to the object
    print("     Adding node sets...")
    m_p_p.add_node_set("Epicardio")
    m_p_p.add_node_set("Endocardio")
    m_p_p.add_node_set("Top_surface")
    
    # Set inital positions obtained by .feb model
    print("     Setting positions...")
    m_p_p.set_initial_positions()
    # Set positions obtained by the simulations
    m_p_p.set_sim_positions(position_nodes_out_file_path)
    
    # Set position data attributed to each data_set (makes run faster since many functions require the data from a node_set)
    print("     Setting node set data (position)...")
    m_p_p.set_node_set_data("Epicardio","position",0)
    m_p_p.set_node_set_data("Endocardio","position",0)
    m_p_p.set_node_set_data("Epicardio","position",m_p_p.len_sim-1)
    m_p_p.set_node_set_data("Endocardio","position",m_p_p.len_sim-1)
    
    # Get Apex and base node. Base node will be a REF node, since it is not contained in mesh
    print("     Getting apex and base from nodes position data...")
    m_p_p.get_apex_and_base_nodes(set_as_properties=True)

    # print(m_p_p.apex_node)

    print("#"*60)
    print("Data information:")
    for node_set in m_p_p.node_sets:
        print("     Number of nodes in '" + node_set + "':", len(m_p_p.node_sets[node_set]))

    # first_data = m_p_p.node_sets_data[next(iter(m_p_p.node_sets_data))][next(iter(m_p_p.node_sets))]["0"]
    # last_data = m_p_p.node_sets_data[next(iter(m_p_p.node_sets_data))][next(iter(m_p_p.node_sets))][str(m_p_p.len_sim-1)]
    # # print("     Number of steps in simulation:",last_data)
    # print("     Number of steps extracted:", m_p_p.len_sim)    
    # for key in m_p_p.node_sets_data:
    #     print("     Data_set_extracted:",key)

    # print("     Initial time in simulation:",first_data["time"])
    # print("     Final time in simulation:",last_data["time"])

    # m_p_p.plot_surface(m_p_p.node_sets_data["position"]["Epicardio"]['0'])
    # m_p_p.plot_surface(m_p_p.node_sets_data["position"]["Endocardio"]['0'],ax=ax)
    # m_p_p.plot_shape()
    
    # ___________________
    # Calculations
    # ___________________
    print("\n" + "#"*60)
    print("Performing Calculations:")
    
    # Calculating Ejection Fraction
    print("     Calculating Ejection Fraction...")
    ejection_fraction, volumes = m_p_p.ejection_fraction()
    
    print("     Calculating Wall Thickness Fraction...")
    wall_th_frac, wall_thickness = m_p_p.thickness_fraction()
    
    print(" Calculating Apex Wall Thickness Fraction...")
    apex_wall_th_frac, apex_wall_thickness = m_p_p.apex_thickness_fraction()
    
    print(" Calculating Radial Shortening...")
    radial_shortening, endo_radius = m_p_p.radial_shortening()
    
    # ___________________
    # Printing / saving results
    # ___________________
    print("\n" + "#"*60)
    print("Results:\n")
    
    print("     Ejection Fraction            = ", ejection_fraction)
    print("     Wall Thickness Fraction      = ", wall_th_frac)
    print("     Apex Wall Thickness Fraction = ", apex_wall_th_frac)
    print("     Radial Shortening            = ", radial_shortening)

    with open(join(o_folder, "results.txt"), "w") as file:

        file.write("Initial Endocardio volume    = " + str(volumes[0]) + "\n")
        file.write("Final Endocardio volume      = " + str(volumes[1]) + "\n")

        file.write("Initial wall thickness       = " + str(wall_thickness[0]) + "\n")
        file.write("Final wall thickness         = " + str(wall_thickness[1]) + "\n")

        file.write("Initial apex wall thickness  = " + str(apex_wall_thickness[0]) + "\n")
        file.write("Final apex wall thickness    = " + str(apex_wall_thickness[1]) + "\n")

        file.write("Initial Endocardio radius    = " + str(endo_radius[0]) + "\n")
        file.write("Final Endocardio radius      = " + str(endo_radius[1]) + "\n")
        
        file.write("Ejection Fraction            = " + str(ejection_fraction) + "\n")
        file.write("Wall Thickness Fraction      = " + str(wall_th_frac) + "\n")
        file.write("Apex Wall Thickness Fraction = " + str(apex_wall_th_frac) + "\n")
        file.write("Radial Shortening            = " + str(radial_shortening) + "\n")
        
    
    # # print(ejection_fraction)
    # # print("hello")
    
