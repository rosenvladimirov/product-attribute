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
        onWidgetReady: { type: Function, optional: true },
        resModel: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            availableFields: [],
            selectedField: this.props.definition.field_name || "",
            selectedValue: this.props.definition.value || "",
        });

        this.loadAvailableFields();

        onWillUpdateProps((nextProps) => {
            this.state.selectedField = nextProps.definition.field_name || "";
            this.state.selectedValue = nextProps.definition.value || "";
            this.loadAvailableFields();
        });
    }

    getFieldIcon(fieldType) {
        const icons = {
            'char': 'fa-font',
            'text': 'fa-file-text-o',
            'integer': 'fa-hashtag',
            'float': 'fa-line-chart',
            'boolean': 'fa-check-square-o',
            'date': 'fa-calendar',
            'datetime': 'fa-clock-o',
            'selection': 'fa-list-ul',
            'many2one': 'fa-link',
            'one2many': 'fa-list',
            'many2many': 'fa-random',
            'binary': 'fa-paperclip',
            'html': 'fa-code',
            'monetary': 'fa-dollar',
            'reference': 'fa-bookmark-o'
        };
        return icons[fieldType] || 'fa-file-o';
    }

    getFieldColor(fieldType) {
        const colors = {
            'char': '#28a745',
            'text': '#6c757d',
            'integer': '#007bff',
            'float': '#17a2b8',
            'boolean': '#ffc107',
            'date': '#fd7e14',
            'datetime': '#e83e8c',
            'selection': '#6f42c1',
            'many2one': '#20c997',
            'one2many': '#dc3545',
            'many2many': '#6610f2',
            'binary': '#6c757d',
            'html': '#fd7e14',
            'monetary': '#28a745',
            'reference': '#17a2b8'
        };
        return colors[fieldType] || '#6c757d';
    }

    get isPropertyDefinitionMode() {
        return !this.props.record || !this.props.record.data;
    }

    getCoModel() {
        if (this.props.record?.resModel) {
            return this.props.record.resModel;
        }

        if (this.env.context?.active_model) {
            return this.env.context.active_model;
        }

        if (this.env.model?.config?.resModel) {
            return this.env.model.config.resModel;
        }

        if (this.env.services?.action?.currentController?.props?.resModel) {
            return this.env.services.action.currentController.props.resModel;
        }

        if (this.env.services?.action?.currentController?.action?.res_model) {
            return this.env.services.action.currentController.action.res_model;
        }

        return "";
    }

    async loadAvailableFields() {
        const comodel = this.getCoModel();

        if (!comodel) {
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
                .map(field => ({
                    name: field.name,
                    description: field.field_description,
                    type: field.ttype,
                    icon: this.getFieldIcon(field.ttype),
                    color: this.getFieldColor(field.ttype)
                }));

        } catch (error) {
            this.state.availableFields = [];
        }
    }

    get selectedFieldLabel() {
        if (!this.state.selectedField) {
            return "Select a field...";
        }

        const field = this.state.availableFields.find(f => f.name === this.state.selectedField);
        return field ? `${field.description} (${field.name})` : this.state.selectedField;
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
        if (!this.state.selectedField) {
            return "No value";
        }

        if (this.isPropertyDefinitionMode) {
            if (!this.state.selectedValue) {
                return "No value";
            }
            return this.state.selectedValue;
        }

        if (!this.props.record?.data) {
            return "No value";
        }

        const recordValue = this.props.record.data[this.state.selectedField];

        if (recordValue === undefined || recordValue === null || recordValue === false || recordValue === '') {
            return "No value";
        }

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

        if (this.isPropertyDefinitionMode) {
            return Boolean(this.state.selectedValue);
        }

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
        try {
            this.state.selectedField = fieldName;

            const updatedDefinition = {
                ...this.props.definition,
                field_name: fieldName,
            };

            if (typeof this.props.onChange === 'function') {
                this.props.onChange(updatedDefinition);
            }
        } catch (error) {
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
