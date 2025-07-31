
/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class PropertiesDefinitionViewer extends Component {
    static template = "properties_fields.PropertiesDefinitionViewer";

    static props = {
        ...standardFieldProps,
        propertiesDefinition: { type: Array, optional: true },
        readonly: { type: Boolean, optional: true },
        onPrintableChange: { type: Function, optional: true },
        onAdd: { type: Function, optional: true },
        onEdit: { type: Function, optional: true },
        onDelete: { type: Function, optional: true },
        onDuplicate: { type: Function, optional: true },
    };

    static extractProps = ({ attrs }, dynamicInfo) => {
        return {
            propertiesDefinition: dynamicInfo.value || [],
            readonly: dynamicInfo.readonly,
            onAdd: (property) => {
                if (dynamicInfo.update) {
                    const newValue = [...(dynamicInfo.value || []), property];
                    dynamicInfo.update(newValue);
                }
            },
            onEdit: (property) => {
                if (dynamicInfo.update && dynamicInfo.value) {
                    const newValue = dynamicInfo.value.map(p =>
                        p.name === property.name ? property : p
                    );
                    dynamicInfo.update(newValue);
                }
            },
            onDelete: (property) => {
                if (dynamicInfo.update && dynamicInfo.value) {
                    const newValue = dynamicInfo.value.filter(p =>
                        p.name !== property.name
                    );
                    dynamicInfo.update(newValue);
                }
            },
            onDuplicate: (property) => {
                if (dynamicInfo.update && dynamicInfo.value) {
                    const newProperty = { ...property };
                    newProperty.name = `${property.name}_copy`;
                    const newValue = [...dynamicInfo.value, newProperty];
                    dynamicInfo.update(newValue);
                }
            },
            onPrintableChange: (propertyName, newValue) => {
                if (dynamicInfo.update && dynamicInfo.value) {
                    const newProperties = dynamicInfo.value.map(p =>
                        p.name === propertyName ? { ...p, printable: newValue } : p
                    );
                    dynamicInfo.update(newProperties);
                }
            },
        };
    };

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            selectedRows: new Set(),
            sortBy: null,
            sortOrder: 'asc',
        });
    }

    get propertiesData() {
        if (!this.props.propertiesDefinition) return [];

        let data = this.props.propertiesDefinition.map(property => ({
            name: property.name || '',
            string: property.string || '',
            type: property.type || '',
            comodel: property.comodel || '',
            default: this.formatDefaultValue(property.default),
            selection: property.selection || [],
            tags: property.tags || [],
            domain: property.domain || '',
            view_in_cards: property.view_in_cards || false,
            printable: property.printable || false,
        }));

        // Apply sorting
        if (this.state.sortBy) {
            data.sort((a, b) => {
                const aVal = a[this.state.sortBy];
                const bVal = b[this.state.sortBy];
                const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
                return this.state.sortOrder === 'asc' ? comparison : -comparison;
            });
        }

        return data;
    }

    formatDefaultValue(defaultValue) {
        if (!defaultValue) return '';
        if (Array.isArray(defaultValue)) {
            return JSON.stringify(defaultValue);
        }
        return String(defaultValue);
    }

    getTypeIcon(type) {
        return `/properties_fields/static/src/views/fields/properties/icons/${type}.png`;
    }

    // Selection methods
    onRowSelect(propertyName, event) {
        if (event.target.checked) {
            this.state.selectedRows.add(propertyName);
        } else {
            this.state.selectedRows.delete(propertyName);
        }
    }

    onSelectAll(event) {
        if (event.target.checked) {
            this.propertiesData.forEach(prop => {
                this.state.selectedRows.add(prop.name);
            });
        } else {
            this.state.selectedRows.clear();
        }
    }

    // Row interaction methods
    onRowClick(property) {
        if (this.state.selectedRows.has(property.name)) {
            this.state.selectedRows.delete(property.name);
        } else {
            this.state.selectedRows.add(property.name);
        }
    }

    onCellClick(property, fieldName) {
        console.log(`Clicked ${fieldName} for property ${property.name}`);
    }

    // CRUD operations
    onAddProperty() {
        if (this.props.onAdd) {
            this.props.onAdd();
        }
    }

    onEditProperty(property) {
        if (this.props.onEdit) {
            this.props.onEdit(property);
        }
    }

    onDuplicateProperty(property) {
        if (this.props.onDuplicate) {
            this.props.onDuplicate(property);
        }
    }

    onDeleteProperty(property) {
        if (this.props.onDelete) {
            this.props.onDelete(property);
        }
    }

    onPrintableToggle(property, event) {
        if (this.props.readonly) return;

        const newValue = event.target.checked;
        if (this.props.onPrintableChange) {
            this.props.onPrintableChange(property.name, newValue);
        }
    }

    // Sorting
    onSort(fieldName) {
        if (this.state.sortBy === fieldName) {
            this.state.sortOrder = this.state.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.sortBy = fieldName;
            this.state.sortOrder = 'asc';
        }
    }
}

// Регистрираме widget-а
registry.category("view_widgets").add("property_definition_viewer", PropertiesDefinitionViewer);
