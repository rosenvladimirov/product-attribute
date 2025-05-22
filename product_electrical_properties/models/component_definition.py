# -*- coding: utf-8 -*-
import os
from random import randint
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET
from odoo import addons, fields, models, _

XML_FILENAME = "component_definition.xml"
UUID_LENGTH = 16


def generate_uuid():
    s = ''
    for i in range(UUID_LENGTH):
        s = s + str(randint(0, 9))
    return (int(s)).to_bytes(8, byteorder='little').hex()


class ComponentsDefinition(models.Model):
    _name = 'component.definition.properties'
    _description = 'Component Definition Properties'
    _rec_name = 'code'

    sequence = fields.Integer('Sequence')
    code = fields.Char('Code')
    name = fields.Char('Name')
    component_properties_definition = fields.PropertiesDefinition('Component Capacitance definitions')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'The code must be unique.'),
    ]

    @staticmethod
    def _get_module_path():
        """
        Determine and return the file system path for the module's associated data directory.

        This method identifies the current module's name and searches for its corresponding directory within the package
        structure of `addons`. If such a directory exists and contains a "data" subdirectory,
        the path to the "data" subdirectory is returned.

        :return: The file system path to the "data" directory associated with the module.
        :rtype: str
        """
        module = __name__.split("addons.")[1].split(".")[0]
        for adp in addons.__path__:
            module_path = os.path.join(adp, module)
            if os.path.isdir(module_path):
                return os.path.join(module_path, "data")
        return ""

    @staticmethod
    def _process_item(item):
        """
        Processes an XML element to extract attribute and text values.

        This method processes a provided XML element and constructs a dictionary
        where the key is the 'name' attribute of the element and the value is its
        corresponding text. If the 'name' attribute does not exist or the text is
        empty, default values are handled accordingly.

        :param item: An XML element from the ElementTree representing a single
                     item node. The element should contain a 'name' attribute.
        :type item: ET.Element
        :return: A dictionary with a single key-value pair where the key is the
                 'name' attribute of the element and the value is the text of the
                 element.
        :rtype: Dict[str, str]
        """
        item_attr = item.attrib
        return {
            item_attr.get('name'): item.text or ''
        }

    def _process_items(self, items):
        """
        Processes a given XML element and extracts its attributes and sub-elements into a dictionary.

        The method takes an XML element, extracts its attributes, and organizes its data into a structured
        dictionary. It also processes nested 'item' elements and combines their data into the resulting
        dictionary.

        :param items: An XML ElementTree element. This element should have attributes and possibly nested
                      'item' nodes which will be processed.
        :return: A dictionary containing the attributes and processed data of the provided XML element.
        :rtype: Dict[str, Any]
        """
        items_attr = items.attrib
        result = {
            'name': generate_uuid(),
            'string': items_attr.get('name')
        }

        for item in items.iter('item'):
            result.update(self._process_item(item))

        return result

    def _process_properties(self, properties, sequence):
        """
        Processes XML 'properties' element and its 'items' children to extract relevant
        attribute data and stores it in a dictionary format. This function encapsulates
        data about the properties and their sequence, returning a structured dictionary
        for further processing.

        :param properties:
            An XML element representing the 'properties' node. It contains attributes
            and child 'items' elements required for processing.
        :type properties: ET.Element
        :param sequence:
            An integer representing the sequence of the properties, which is included
            in the returned dictionary.
        :type sequence: int
        :return:
            A dictionary containing the processed data. This includes the sequence,
            attributes from the 'properties' element like 'code' and 'name', and parsed
            data from its child 'items' elements.
        :rtype: Dict[str, Any]
        """
        properties_attrib = properties.attrib
        component_props = []

        for items in properties.iter('items'):
            component_props.append(self._process_items(items))

        return {
            'sequence': sequence,
            'code': properties_attrib.get('code'),
            'name': properties_attrib.get('name'),
            'component_properties_definition': component_props,
        }

    def create_component_properties_definition(self, codes=False):
        """
        Creates a definition of component properties by processing the data from an XML
        file and manipulating the records in the database. This function processes a set
        of XML property records, removes the existing definitions that match specified
        codes (if provided), and creates new records based on the parsed values.

        :param codes: An optional list of strings representing the codes of properties to
            be processed. If provided, only properties whose code matches the codes in
            this list will be processed. If set to False, all properties will be
            processed.
        :type codes: Optional[List[str]]

        :return: Newly created database records for component properties.
        :rtype: Model
        """
        module_path = self._get_module_path()
        xml_file = ET.parse(os.path.join(module_path, XML_FILENAME))
        records = xml_file.getroot().find("properties")

        values = []
        for sequence, properties in enumerate(records.iter("properties")):
            if codes and properties.attrib.get('code') not in codes:
                continue
            values.append(self._process_properties(properties, sequence))

        record_to_delete = self.env['component.definition.properties']
        for value in values:
            if value.get('code'):
                record_to_delete |= self.search([('code', '=', value['code'])])

        if record_to_delete:
            record_to_delete.unlink()

        return self.create(values)
