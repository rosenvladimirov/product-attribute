/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PropertyValue } from "@web/views/fields/properties/property_value";

patch(PropertyValue.prototype, {
    setup() {
        super.setup();
    },

    _isFieldsType() {
        return this.props.type === "fields" || (this.props.definition && this.props.definition.type === "fields");
    },

    get displayValue() {
        if (this._isFieldsType()) {
            return this.props.value;
        }

        return super.displayValue;
    },
});
