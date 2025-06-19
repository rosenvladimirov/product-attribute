# -*- coding: utf-8 -*-
import os
from random import randint
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET
from odoo import addons, fields, models, _
from odoo.exceptions import UserError

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

        :param item: An XML element from the ElementTree is representing a single
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
        try:
            module_path = self._get_module_path()
            xml_path = os.path.join(module_path, XML_FILENAME)

            if not os.path.exists(xml_path):
                raise FileNotFoundError(f"XML file not found: {xml_path}")

            xml_file = ET.parse(xml_path)
            records = xml_file.getroot()

            values = []
            for sequence, properties in enumerate(records.iter("properties")):
                code = properties.attrib.get('code')
                if codes and code not in codes:
                    continue
                values.append(self._process_properties(properties, sequence))

            if values:
                codes_to_delete = [v['code'] for v in values if v.get('code')]
                if codes_to_delete:
                    records_to_delete = self.search([('code', 'in', codes_to_delete)])
                    records_to_delete.unlink()

            return self.create(values)

        except (IOError, ET.ParseError) as e:
            raise UserError(f"Error processing XML file: {str(e)}")
