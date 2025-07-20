/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PropertyValue } from "@web/views/fields/properties/property_value";
import { ModelFieldsWidget } from "@properties_fields/views/fields/properties/extended_properties_field";

patch(PropertyValue.prototype, {
    /**
     * Return the value of the current property,
     * that will be used by the sub-components.
     *
     * @returns {object}
     */
    get propertyValue() {
        const value = this.props.value;

        if (this.props.type === "fields") {
            // Връщаме стойността от полето на записа
            return this.getFieldValueFromRecord();
        }

        // За всички останали типове използваме оригиналната логика
        return super.propertyValue;
    },

    /**
     * Get the field value from the current record.
     * Used for "fields" type properties.
     *
     * @returns {any}
     */
    getFieldValueFromRecord() {
        // Временно използваме string като field_name, докато не се добави правилното поле
        const fieldName = this.props.field_name || this.props.string.toLowerCase().replace(/\s+/g, '_');

        if (!fieldName || !this.props.record) {
            console.warn('Missing field_name or record for fields type property:', this.props);
            return null;
        }

        const fieldValue = this.props.value || this.props.record.data[fieldName];

        if (fieldValue === undefined || fieldValue === null) {
            return null;
        }

        return fieldValue;
    },

    /**
     * Handle changes from ModelFieldsWidget
     * @param {Object} updatedDefinition
     */
    onModelFieldsDefinitionChange(updatedDefinition) {
        // Обновяваме цялата definition, включително field_name
        this.onValueChange(updatedDefinition);
    },

    /**
     * Formatted value displayed in readonly mode.
     *
     * @returns {string}
     */
    get displayValue() {
        // ДОБАВЯМЕ обработка за fields тип
        if (this.props.type === "fields") {
            const value = this.propertyValue;

            if (!value) {
                return false;
            }

            const fieldType = this.props.field_type || 'char';
            return this.formatFieldValue(value, fieldType);
        }

        // За всички останали типове използваме оригиналната логика
        return super.displayValue;
    },

    /**
     * Format field value based on its type.
     *
     * @param {any} value
     * @param {string} fieldType
     * @returns {string}
     */
    formatFieldValue(value, fieldType) {
        if (value === null || value === undefined || value === false) {
            return "No value";
        }

        switch (fieldType) {
            case 'boolean':
                return value ? "Yes" : "No";

            case 'integer':
                return formatInteger(value);

            case 'float':
            case 'monetary':
                return formatFloat(value);

            case 'date':
                return formatDate(value);

            case 'datetime':
                return formatDateTime(value);

            case 'char':
            case 'text':
            case 'html':
                return value.toString();

            default:
                return value.toString();
        }
    },

    /**
     * Debug method to log props
     */
    setup() {
        super.setup();
        console.log('PropertyValue props:', this.props);
        console.log('PropertyValue definition:', this.props.definition);
    }

});

// Добавяме компонента към PropertyValue
PropertyValue.components = {
    ...PropertyValue.components,
    ModelFieldsWidget
};
