# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Hook executed before module installation"""
    _patch_properties_field()


def post_init_hook(env):
    """Hook executed after module installation"""
    _patch_properties_field()


def _patch_properties_field():
    """Patch Properties field to support fields type"""
    from odoo.fields import Properties, PropertiesDefinition

    # Само веднъж patch-ваме
    if hasattr(Properties, '_fields_patch_applied'):
        return

    _logger.info("Applying Properties field patch...")

    # Разширяваме ALLOWED_TYPES за да включи fields
    if hasattr(Properties, 'ALLOWED_TYPES'):
        original_allowed_types = Properties.ALLOWED_TYPES
        Properties.ALLOWED_TYPES = original_allowed_types + ('fields',)
        _logger.info("Extended ALLOWED_TYPES: %s", Properties.ALLOWED_TYPES)

    # Разширяваме ALLOWED_KEYS за да включи field_name и field_type
    if hasattr(PropertiesDefinition, 'ALLOWED_KEYS'):
        original_allowed_keys = PropertiesDefinition.ALLOWED_KEYS
        PropertiesDefinition.ALLOWED_KEYS = original_allowed_keys + ('field_name', 'field_type', 'printable', )
        _logger.info("Extended ALLOWED_KEYS: %s", PropertiesDefinition.ALLOWED_KEYS)

    # Monkey patch на _parse_json_types метода
    original_parse_json_types = Properties._parse_json_types

    def _extended_parse_json_types(values_list, env, res_ids_per_model):
        """Extended version that handles fields type"""
        _logger.info("_parse_json_types called with %d properties", len(values_list))

        # Първо обработваме fields типа, преди да извикаме оригиналния метод
        for property_definition in values_list:
            property_type = property_definition.get('type')
            property_name = property_definition.get('name')

            if property_type == 'fields':
                field_name = property_definition.get('field_name')

                _logger.info("Processing fields property: name=%s, field_name=%s",
                             property_name, field_name)

                # За fields типа запазваме field_name в собствен ключ
                if not field_name:
                    _logger.warning("Missing field_name for fields property")
                    property_definition['field_name'] = False
                    property_definition['field_type'] = False
                    property_definition['value'] = False
                else:
                    # Запазваме field_name в собствен ключ
                    property_definition['field_name'] = field_name
                    property_definition['field_type'] = False  # Ще се попълни в convert_to_read_multi
                    property_definition['value'] = False  # Ще се попълни в convert_to_read_multi
                    _logger.info("Fields property field_name set to: %s", field_name)

        # Сега извикваме оригиналния метод за всички типове (включително fields)
        _logger.info("Calling original _parse_json_types...")
        original_parse_json_types(values_list, env, res_ids_per_model)
        _logger.info("Original _parse_json_types completed")

    # Заменяме метода и го правим статичен
    Properties._parse_json_types = staticmethod(_extended_parse_json_types)

    # Monkey patch на convert_to_read_multi метода
    original_convert_to_read_multi = Properties.convert_to_read_multi

    def _extended_convert_to_read_multi(self, values, records):
        """Extended version that populates fields type values"""
        _logger.info("convert_to_read_multi called with %d records", len(records) if records else 0)

        # Първо извикваме оригиналния метод
        result = original_convert_to_read_multi(self, values, records)
        _logger.info("Original convert_to_read_multi returned %d results", len(result))

        # Само ако има записи
        if not records:
            return result

        # След това попълваме стойностите за fields типа
        for record, value_list in zip(records, result):
            _logger.info("Processing record %s (model: %s) with %d properties",
                         record.id, record._name, len(value_list))

            for property_definition in value_list:
                property_type = property_definition.get('type')
                property_name = property_definition.get('name')

                if property_type == 'fields':
                    # За fields типа, field_name е в собствен ключ
                    field_name = property_definition.get('field_name')

                    _logger.info("Processing fields property: name=%s, field_name=%s",
                                 property_name, field_name)

                    if not field_name:
                        _logger.warning("Missing field_name for fields property")
                        property_definition['value'] = False
                        property_definition['field_type'] = False
                        property_definition['field_name'] = False
                        continue

                    try:
                        # Използваме текущия запис директно
                        if hasattr(record, field_name):
                            field_value = getattr(record, field_name)
                            _logger.info("Field %s value: %s (type: %s)", field_name, field_value, type(field_value))

                            # Вземаме типа на полето от модела
                            model_field = record._fields.get(field_name)
                            if model_field:
                                field_type = model_field.type
                                _logger.info("Field %s type: %s", field_name, field_type)

                                # ВАЖНО: Добавяме field_type и field_name ДИРЕКТНО В property_definition
                                # Това ще ги прехвърли към JavaScript като props
                                property_definition['field_type'] = field_type
                                property_definition['field_name'] = field_name

                                # Конвертираме стойността според типа
                                if field_value is False or field_value is None:
                                    property_definition['value'] = False
                                else:
                                    if field_type in ('char', 'text', 'html'):
                                        property_definition['value'] = str(field_value) if field_value else False
                                    elif field_type in ('integer', 'float', 'monetary'):
                                        property_definition['value'] = field_value
                                    elif field_type == 'boolean':
                                        property_definition['value'] = bool(field_value)
                                    elif field_type in ('date', 'datetime'):
                                        property_definition['value'] = field_value.isoformat() if field_value else False
                                    elif field_type == 'selection':
                                        property_definition['value'] = field_value
                                    elif field_type in ('many2one', 'many2many'):
                                        if field_type == 'many2one':
                                            property_definition['value'] = field_value.id if field_value else False
                                        else:  # many2many
                                            property_definition['value'] = field_value.ids if field_value else []
                                    else:
                                        property_definition['value'] = str(field_value) if field_value else False

                                _logger.info("FINAL property_definition for JavaScript: %s", property_definition)
                            else:
                                property_definition['value'] = str(field_value) if field_value else False
                                property_definition['field_type'] = 'unknown'
                                property_definition['field_name'] = field_name
                                _logger.info("No field definition found, using string conversion: %s",
                                             property_definition['value'])
                        else:
                            _logger.warning("Field %s not found in record %s", field_name, record)
                            property_definition['value'] = False
                            property_definition['field_type'] = False
                            property_definition['field_name'] = field_name
                    except Exception as e:
                        _logger.error("Error reading field %s from record %s: %s", field_name, record, e)
                        property_definition['value'] = False
                        property_definition['field_type'] = False
                        property_definition['field_name'] = field_name

        _logger.info(f"convert_to_read_multi completed with {len(result)} results")
        return result

    # Заменяме метода
    Properties.convert_to_read_multi = _extended_convert_to_read_multi

    # Маркираме че patch-ът е приложен
    Properties._fields_patch_applied = True
    _logger.info("Properties field patch applied successfully")


# Patch-ваме при import на модула
_patch_properties_field()
