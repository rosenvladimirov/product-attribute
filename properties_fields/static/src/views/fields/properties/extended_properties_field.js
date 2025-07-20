/** @odoo-module **/

import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class ModelFieldsWidget extends Component {
    static template = "properties_fields.ModelFieldsWidget";
    static components = { Dropdown, DropdownItem };
    static props = {
        definition: Object,
        onChange: Function,
        record: { type: Object, optional: true },
        context: { type: Object, optional: true },
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            availableFields: [],
            selectedField: this.props.definition.field_name || "",
            selectedValue: this.props.definition.value || "",
        });

        console.log("Initial state:", this.state);
        this.loadAvailableFields();

        onWillUpdateProps((nextProps) => {
            console.log("=== onWillUpdateProps ===");
            console.log("nextProps:", nextProps);
            this.state.selectedField = nextProps.definition.field_name || "";
            this.state.selectedValue = nextProps.definition.value || "";
            this.loadAvailableFields();
        });
    }

    getFieldIcon(fieldType) {
        if (fieldType === 'char') return 'fa-font';
        if (fieldType === 'text') return 'fa-file-text-o';
        if (fieldType === 'integer') return 'fa-hashtag';
        if (fieldType === 'float') return 'fa-line-chart';
        if (fieldType === 'boolean') return 'fa-check-square-o';
        if (fieldType === 'date') return 'fa-calendar';
        if (fieldType === 'datetime') return 'fa-clock-o';
        if (fieldType === 'selection') return 'fa-list-ul';
        if (fieldType === 'many2one') return 'fa-link';
        if (fieldType === 'one2many') return 'fa-list';
        if (fieldType === 'many2many') return 'fa-random';
        if (fieldType === 'binary') return 'fa-paperclip';
        if (fieldType === 'html') return 'fa-code';
        if (fieldType === 'monetary') return 'fa-dollar';
        if (fieldType === 'reference') return 'fa-bookmark-o';
        return 'fa-file-o';
    }

    getFieldColor(fieldType) {
        if (fieldType === 'char') return '#28a745';
        if (fieldType === 'text') return '#6c757d';
        if (fieldType === 'integer') return '#007bff';
        if (fieldType === 'float') return '#17a2b8';
        if (fieldType === 'boolean') return '#ffc107';
        if (fieldType === 'date') return '#fd7e14';
        if (fieldType === 'datetime') return '#e83e8c';
        if (fieldType === 'selection') return '#6f42c1';
        if (fieldType === 'many2one') return '#20c997';
        if (fieldType === 'one2many') return '#dc3545';
        if (fieldType === 'many2many') return '#6610f2';
        if (fieldType === 'binary') return '#6c757d';
        if (fieldType === 'html') return '#fd7e14';
        if (fieldType === 'monetary') return '#28a745';
        if (fieldType === 'reference') return '#17a2b8';
        return '#6c757d';
    }

    get isPropertyDefinitionMode() {
        const result = !this.props.record || !this.props.record.data;
        console.log("isPropertyDefinitionMode:", result);
        return result;
    }

    getCoModel() {
        // Опит 1: от props.record
        if (this.props.record?.resModel) {
            console.log("Got model from props.record:", this.props.record.resModel);
            return this.props.record.resModel;
        }

        // Опит 2: от context (ако има)
        if (this.env.context?.active_model) {
            console.log("Got model from env.context:", this.env.context.active_model);
            return this.env.context.active_model;
        }

        // Опит 3: от env.model
        if (this.env.model?.config?.resModel) {
            console.log("Got model from env.model:", this.env.model.config.resModel);
            return this.env.model.config.resModel;
        }

        // Опит 4: от env.services
        if (this.env.services?.action?.currentController?.props?.resModel) {
            console.log("Got model from env.services:", this.env.services.action.currentController.props.resModel);
            return this.env.services.action.currentController.props.resModel;
        }

        // Опит 5: от env.services.action.currentController.action
        if (this.env.services?.action?.currentController?.action?.res_model) {
            console.log("Got model from action:", this.env.services.action.currentController.action.res_model);
            return this.env.services.action.currentController.action.res_model;
        }

        console.log("No model detected");
        return "";
    }

    async loadAvailableFields() {
        const comodel = this.getCoModel();
        console.log("Final detected model:", comodel);

        if (!comodel) {
            console.log("No model detected, clearing fields");
            this.state.availableFields = [];
            return;
        }

        try {
            const fields = await this.orm.call(
                "ir.model.fields",
                "search_read",
                [
                    [
                        ["model", "=", comodel],
                        ["name", "not in", ["id", "create_uid", "create_date", "write_uid", "write_date", "__last_update"]],
                        ["ttype", "not in", ["many2one", "one2many", "many2many"]]
                    ],
                    ["name", "field_description", "ttype"]
                ]
            );

            this.state.availableFields = fields
                .filter(field => !field.name.startsWith("_"))
                .map(field => {
                    return {
                        name: field.name,
                        description: field.field_description,
                        type: field.ttype,
                        icon: this.getFieldIcon(field.ttype),
                        color: this.getFieldColor(field.ttype)
                    };
                });

            console.log("Available fields:", this.state.availableFields);
            console.log("Available fields count:", this.state.availableFields.length);

            // Ако има поле в definition, но не е в availableFields, нека го проверим
            if (this.state.selectedField && this.state.availableFields.length > 0) {
                const foundField = this.state.availableFields.find(f => f.name === this.state.selectedField);
                console.log("Selected field found in available fields:", foundField);
            }
        } catch (error) {
            console.error("Error loading fields:", error);
            this.state.availableFields = [];
        }
    }

    get selectedFieldLabel() {
        console.log("=== selectedFieldLabel ===");
        console.log("selectedField:", this.state.selectedField);
        console.log("availableFields count:", this.state.availableFields.length);

        if (!this.state.selectedField) {
            console.log("No selected field, returning 'Select a field...'");
            return "Select a field...";
        }

        const field = this.state.availableFields.find(f => f.name === this.state.selectedField);
        console.log("Found field:", field);

        const result = field ? field.description + " (" + field.name + ")" : this.state.selectedField;
        console.log("selectedFieldLabel result:", result);
        return result;
    }

    get selectedFieldIcon() {
        if (!this.state.selectedField) {
            return 'fa-file-o';
        }

        const field = this.state.availableFields.find(f => f.name === this.state.selectedField);
        return field ? field.icon : 'fa-file-o';
    }

    get selectedFieldColor() {
        if (!this.state.selectedField) {
            return '#6c757d';
        }

        const field = this.state.availableFields.find(f => f.name === this.state.selectedField);
        return field ? field.color : '#6c757d';
    }

    get currentFieldValue() {
        console.log("=== currentFieldValue ===");
        console.log("selectedField:", this.state.selectedField);
        console.log("isPropertyDefinitionMode:", this.isPropertyDefinitionMode);

        if (!this.state.selectedField) {
            return "No value";
        }

        // В PropertyDefinition режим - използваме definition.value
        if (this.isPropertyDefinitionMode) {
            console.log("Using definition.value:", this.state.selectedValue);
            if (!this.state.selectedValue) {
                return "No value";
            }
            return this.state.selectedValue;
        }

        // В normal field режим - използваме стойността от записа
        if (!this.props.record?.data) {
            return "No value";
        }

        const recordValue = this.props.record.data[this.state.selectedField];
        console.log("Using record value:", recordValue);

        if (recordValue === undefined || recordValue === null || recordValue === false || recordValue === '') {
            return "No value";
        }

        // Форматираме стойността според типа на полето
        const field = this.state.availableFields.find(f => f.name === this.state.selectedField);
        if (field) {
            return this.formatFieldValue(recordValue, field.type);
        }

        return recordValue.toString();
    }

    get hasValue() {
        if (!this.state.selectedField) {
            return false;
        }

        // В PropertyDefinition режим - проверяваме definition.value
        if (this.isPropertyDefinitionMode) {
            return Boolean(this.state.selectedValue);
        }

        // В normal field режим - проверяваме стойността от записа
        if (!this.props.record?.data) {
            return false;
        }

        const recordValue = this.props.record.data[this.state.selectedField];
        return recordValue !== undefined && recordValue !== null && recordValue !== false && recordValue !== '';
    }

    formatFieldValue(value, fieldType) {
        if (value === null || value === undefined || value === false) {
            return "No value";
        }

        switch (fieldType) {
            case 'boolean':
                return value ? "Yes" : "No";
            case 'date':
                return value.toString();
            case 'datetime':
                return value.toString();
            case 'float':
            case 'monetary':
                return parseFloat(value).toFixed(2);
            case 'integer':
                return parseInt(value).toString();
            default:
                return value.toString();
        }
    }

    onFieldSelect(fieldName) {
        console.log("=== onFieldSelect ===");
        console.log("Selected field:", fieldName);
        console.log("Current definition:", this.props.definition);
        console.log("onChange function:", this.props.onChange);
        console.log("typeof onChange:", typeof this.props.onChange);

        try {
            // Обновяваме state-а
            this.state.selectedField = fieldName;

            // Намираме детайлите на избраното поле
            const selectedField = this.state.availableFields.find(field => field.name === fieldName);
            console.log("Selected field details:", selectedField);

            // Създаваме обновената дефиниция
            const updatedDefinition = {
                ...this.props.definition,
                field_name: fieldName,
                field_type: selectedField ? selectedField.type : 'char'
            };

            console.log("Updated definition:", updatedDefinition);
            console.log("About to call onChange...");

            // Извикваме callback-а с проверка
            if (typeof this.props.onChange === 'function') {
                this.props.onChange(updatedDefinition);
                console.log("onChange called successfully");
            } else {
                console.error("onChange is not a function!", this.props.onChange);
            }
        } catch (error) {
            console.error("ERROR in onFieldSelect:", error);
            console.error("Error message:", error.message);
            console.error("Error stack:", error.stack);

            // Опитваме се да покажем грешката в UI
            if (this.env.services && this.env.services.notification) {
                this.env.services.notification.add(
                    "Error selecting field: " + error.message,
                    { type: "danger" }
                );
            }
        }
    }
}

registry.category("components").add("ModelFieldsWidget", ModelFieldsWidget);
