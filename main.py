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
    # Set inital positions obtained by .feb model
    myo_post_process.set_initial_positions()
    # Set positions obtained by the simulations
    myo_post_process.set_sim_positions(position_nodes_out_file_path)
    
    myo_post_process.get_apex_and_base_nodes()
    print("Apex:")
    pp(myo_post_process.apex_nodes)
    print("Base:")
    pp(myo_post_process.base_nodes)
    


    # ___________________
    # Calculations
    # ___________________
    
    # Calculating Ejection Fraction
    ejection_fraction = myo_post_process.ejection_fraction()
    print(ejection_fraction)
    print("hello")
    
