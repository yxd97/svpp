from enum import Enum
from typing import List
import xml.etree.ElementTree as ET

class Port:
    def __init__(self, element:ET.Element):
        self.name = element.attrib["name"]
        self.mode = element.attrib["mode"]
        self.type = element.attrib["portType"]
        self.data_width = int(element.attrib["dataWidth"])
        self.base = int(element.attrib["base"], base=16)
        self.range = int(element.attrib["range"], base=16)

    def __str__(self):
        return f"{self.type} {self.mode} {self.name}"


class KernelArgument:
    def __init__(self, element:ET.Element):
        self.name = element.attrib["name"]
        self.type = element.attrib["type"]
        self.is_pointer = element.attrib["addressQualifier"] == "1"
        self.port_name = element.attrib["port"]
        self.size = int(element.attrib["size"], base=16)
        self.offset = int(element.attrib["offset"], base=16)

    def __str__(self):
        return f"{self.type} {self.name}"


class KernelSignature:
    def __init__(self, element:ET.Element):
        kernel_def = element.find("kernel")
        self.name = kernel_def.attrib["name"]
        self.protocol = kernel_def.attrib["hwControlProtocol"]
        self.use_interrupt = kernel_def.attrib["interrupt"] == "true"
        self.ports = {
            port.attrib["name"]: Port(port) for port in kernel_def.find("ports")
        }
        self.args = [
            KernelArgument(arg) for arg in kernel_def.find("args")
        ]

    def __str__(self):
        csig = f"{self.name}({', '.join([str(arg) for arg in self.args])});"
        portmap = '\n'.join([f"{arg.name} : {self.ports[arg.port_name].name}" for arg in self.args])
        return f"{csig}\n/*\n{portmap}\n*/"

    def __repr__(self):
        return str(self)


if __name__ == "__main__":
    build_dir = "tests/build_hw_xilinx_u280_gen3x16_xdma_1_202211_1"
    kernel_name = "vvadd"
    xml = f"{build_dir}/{kernel_name}/{kernel_name}/{kernel_name}/kernel.xml"
    sig = KernelSignature(ET.parse(xml).getroot())
    print(sig)