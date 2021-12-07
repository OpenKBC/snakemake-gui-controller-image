__author__ = "Junhee Yoon"
__version__ = "1.0.4"
__maintainer__ = "Junhee Yoon"
__email__ = "swiri021@gmail.com"


import yaml
import collections
from omegaconf import OmegaConf

class yamlHandlers(object):
    # Parsing function for yaml data, only work 2 layer nested yaml file
    def _parsing_yamlFile(workflow_path, yamlfilename="config.yaml"):
        """
        Description: This function parses yaml format in config.yaml, and returns dictionary with parse data
        
        Input: yaml path
        Output: Dictionary with parse data
        """
        
        ## yaml check
        ## yaml check
        with open(workflow_path+"/"+yamlfilename, "r") as stream: # Open yaml
            try:
                yaml_data = yaml.safe_load(stream) # Parse auto with pyyaml
            except yaml.YAMLError as exc:
                print(exc)
        
        new_result = {} # for new result dictionary
        for key, value in yaml_data.items():
            if isinstance(value, dict)==True: # Nested dictionary
                for nkey, nval in value.items(): # Only key name for making form
                    new_result[key+"--"+nkey] = nval # Nested key has '--', making flatten
            else:
                new_result[key]=value #just pass with normal dictionary
        return new_result
    
    def _parsing_yamlFile_omega(workflow_path, yamlfilename="config.yaml"):
        conf = OmegaConf.load(workflow_path+"/"+yamlfilename)
        return(conf)

    # Custom yaml converting function because of pyyaml unexpected charter
    def _reform_yamlFile(selected_pipeline, data_dict, created_name):
        """
        Description: This function converts dictionary to yaml for snakemake, and write yaml file on the path
        
        Input: pipeline path and dictionary data
        Output: yaml file
        """
        # Write new yaml file
        yamlFileName = selected_pipeline+"/config_"+created_name+".yaml"
        f = open(yamlFileName, "w") # write file with unique name

        # Collection for nested dictionary
        parsed_dict=collections.defaultdict(dict)

        for key, val in data_dict.items():
            # If key has nested keys
            if "--" in key:
                temp = key.split("--") # 0=masterkey, 1=subkey
                parsed_dict[temp[0]][temp[1]]=val
            else:
                parsed_dict[key]=val
        parsed_dict = dict(parsed_dict) # Convert to normal dictionary
        yaml_string = OmegaConf.to_yaml(parsed_dict) # Convert to Yaml
        f.write(yaml_string.strip()) # Write file
        f.close()

        return yamlFileName