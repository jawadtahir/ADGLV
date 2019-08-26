'''
Created on May 21, 2019

@author: foobar
'''
import os
from pathlib import Path

import yaml

from config import Config
from nodes import Nodes


def generate():
    project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
    nodes_yaml_path = os.path.join(project_root, "config", "nodes.yaml")
    config_yaml_path = os.path.join(project_root, "config", "config.yaml")

    print(nodes_yaml_path)
    print(config_yaml_path)
    print(project_root)

    nodes = Nodes()
    config = Config()

    node_file = open(nodes_yaml_path, "w")
    config_file = open(config_yaml_path, "w")

    yaml.dump(nodes.__dict__, node_file, default_flow_style=False)
    yaml.dump(config.__dict__, config_file, default_flow_style=False)


#     config = Config()
#     config.name = "test"
# #     config.nodes_list = nodes.nodes_list.keys()
# #     config.nodes_map = nodes.nodes_list
#
#     yaml.dump(config.__dict__, config_file)
#     yaml.dump(nodes, y_file)


if __name__ == '__main__':
    generate()
