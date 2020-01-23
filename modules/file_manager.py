


def read_feb_out_txt_file(file_path):
    with open(file_path, mode="r") as txt_file:
        output = []
        
        has_structure = False
        
        header_boolean_0 = False
        header_boolean_1 = False
        
        idx = int(-1)
        
        # try:
        for line in txt_file:
                            
            line = line.rstrip().lstrip().strip(' ')
            if line[0] == "*":
                header_boolean_1 = True
                
                if header_boolean_1 != header_boolean_0:
                    # print("TRUE AT LINE:")
                    # print(line)
                    
                    data = {
                        "step": 0,
                        "time": 0,
                        "struct": [],
                        "nodes": {},
                        "val": None
                    }
                    output.append(data)
                    idx += 1                
                
                info = line.split("= ")
                if info[0].lower().find("step") > -1:
                    output[idx]["step"] = int(info[1])
                elif info[0].lower().find("time") > -1:
                    output[idx]["time"] = float(info[1])
                elif info[0].lower().find("data") > -1:
                    has_structure = True
                    output[idx]["struct"] = info[1].split(";")
            else:
                header_boolean_1 = False
                
                data_line = line.split(",")
                if has_structure:
                    val = {"node": data_line[0]}
                    # print(data_line)
                    for i in range(0,len(data_line[1:])):
                        key = data["struct"][i]
                        val[key] = data_line[i+1]
                    output[idx]["nodes"][str(data_line[0])] = val
                    # print(val)
                else:
                    output[idx]["val"] = data_line
                    
            header_boolean_0 = header_boolean_1
        return output
    
def read_csv(self,file_path):
    with open(file_path, mode='r') as csv_file:
        try:
            csv_file_reader = csv.reader(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            data = []
            for row in csv_file_reader:
                data.append(row)
            return data
        except:
            raise(ValueError('Error reading csv file.\n'))  
        
def get_nodes_from_nodeset(doc,node_set_name):
        """
            Extract nodes from nodeset in a .feb file by extracting the Nodesets and comparing the name atrr.
        """
        # Extracting elements with tag names = 'NodeSet'
        node_sets = doc.getElementsByTagName("NodeSet")
        # Looping through array to find desired NodeSet
        for node_set in node_sets:
            # Getting the name of the node_set element
            name = node_set.attributes['name'].value
            # If the name matches, extract all the nodes and return
            if name == node_set_name:
                # Extracting elements with 
                node_elems = node_set.getElementsByTagName("node")
                nodes = []
                for node in node_elems:
                    nodes.append(int(node.attributes['id'].value))

                nodes = sorted(nodes)

                return nodes          
            
def load_by_tag(doc_file,tag):
    """ 
        Function used to load desired elements from xml file using their tag attribute
        Reuires:
            doc_file: Path to file document (string)
            tag: Name of desired tag to be found (string)
        Returns:
            nodes: Array of nodes of requested tag attributes
    """
    # print("Loading: '" + str(tag) + "'")
    file_nodes = doc_file.getElementsByTagName(tag)
    if len(file_nodes) != 0:
        nodes = []
        idx = 1
        l = len(file_nodes)
        for node in file_nodes:
            try:
                _nodes = [int(node.attributes['id'].value)]
            except:
                _nodes = [idx]

            try:
                _nodes.extend([float(i) for i in node.firstChild.nodeValue.split(',')])
                nodes.append(_nodes)
            except:
                pass
            idx += 1

        return nodes
    else:
        raise(ValueError('No tag "'+ str(tag) + '" identified.'))