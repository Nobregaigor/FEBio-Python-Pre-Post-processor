from modules import *
from pprint import pprint as pp
if __name__ == "__main__":
    
    # ___________________
    # File Paths
    # ___________________
    myo_feb_file_path = "input/LinearConstrainTest3_1.feb"
    position_nodes_out_file_path = "input/simulation_outputs/position_node_out.txt"
    
    # ___________________
    # Creating Object for Post Process
    # ___________________
    
    # Storing the Post process at location defined by myo_post_process
    myo_post_process = FEBio_post_process()
    
    # Creating a doc for the desired post process file
    myo_post_process.create_doc(myo_feb_file_path)
    # Adding NodeSets to the object
    myo_post_process.add_node_set("Epicardio")
    myo_post_process.add_node_set("Endocardio")
    myo_post_process.add_node_set("Top_surface")
    # Set positions obtained by the simulations
    
    pos = myo_post_process.set_initial_positions()
    myo_post_process.set_sim_positions(position_nodes_out_file_path)
    
    