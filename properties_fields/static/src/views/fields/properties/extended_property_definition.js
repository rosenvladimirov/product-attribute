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
        // Добавяме новия тип "fields" към списъка
        const fieldsType = ["fields", _t("Model Fields")];
        return [...types, fieldsType];
    },

    onPropertyTypeChange(newType) {
        console.log("=== onPropertyTypeChange ===");
        console.log("newType:", newType);

        if (newType === "fields") {
            const propertyDefinition = {
                ...this.state.propertyDefinition,
                type: newType,
                value: false,
                field_name: "",
                default: false,
            };

            console.log("Final propertyDefinition:", propertyDefinition);

            this.props.onChange(propertyDefinition);
            this.state.propertyDefinition = propertyDefinition;
            this.state.resModel = "";
            this.state.resModelDescription = "";
            this.state.typeLabel = this._typeLabel(newType);
        } else {
            // За всички други типове използваме оригиналната логика
            super.onPropertyTypeChange(newType);
        }
    },

    onModelFieldsDefinitionChange(definition) {
        console.log("onModelFieldsDefinitionChange called with:", definition);
        console.log("Current state.propertyDefinition:", this.state.propertyDefinition);

        this.state.propertyDefinition = {
            ...this.state.propertyDefinition,
            ...definition
        };

        console.log("Updated state.propertyDefinition:", this.state.propertyDefinition);
        this.props.onChange(this.state.propertyDefinition);
    },
});
