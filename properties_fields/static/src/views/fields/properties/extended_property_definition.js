/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PropertyDefinition } from "@web/views/fields/properties/property_definition";
import { ModelFieldsWidget } from "@properties_fields/views/fields/properties/extended_properties_field";

patch(PropertyDefinition.prototype, {
    setup() {
        super.setup();
        this.constructor.components = {
            ...this.constructor.components,
            ModelFieldsWidget,
        };
    },

    get availablePropertyTypes() {
        const types = super.availablePropertyTypes;
        const fieldsType = ["fields", _t("Model Fields")];
        return [...types, fieldsType];
    },

    get propertyValueProps() {
        const baseProps = super.propertyValueProps || {};

        return {
            ...baseProps,
            fieldName: this.state.propertyDefinition?.field_name,
            propertyDefinitionState: this.state,
        };
    },

    onPropertyTypeChange(newType) {
        if (newType === "fields") {
            const propertyDefinition = {
                ...this.state.propertyDefinition,
                type: newType,
                value: false,
                field_name: "",
                default: false,
                printable: false, // Добавяме printable свойство
            };

            this.props.onChange(propertyDefinition);
            this.state.propertyDefinition = propertyDefinition;
            this.state.resModel = "";
            this.state.resModelDescription = "";
            this.state.typeLabel = this._typeLabel(newType);
        } else {
            super.onPropertyTypeChange(newType);
        }
    },

    onModelFieldsDefinitionChange(definition) {
        this.state.propertyDefinition = {
            ...this.state.propertyDefinition,
            ...definition
        };

        this.props.onChange(this.state.propertyDefinition);
    },

    // Нов метод за обработка на промяната в checkbox-а
    onPrintableChange(newValue) {
        const propertyDefinition = {
            ...this.state.propertyDefinition,
            printable: newValue,
        };

        this.props.onChange(propertyDefinition);
        this.state.propertyDefinition = propertyDefinition;
    },
});
