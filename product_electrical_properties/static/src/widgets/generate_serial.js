/** @odoo-module */

import { GenerateDialog } from "@stock/widgets/generate_serial";
import { patch } from "@web/core/utils/patch";
import { useRef } from "@odoo/owl";

patch(GenerateDialog.prototype, {
    /**
     * Initializes the setup process by calling the original setup method and adding additional references.
     * This method makes use of `useRef` to create specific references for `dataCode` and `dataCodeImport`.
     *
     * @return {void} This method does not return any value.
     */
    setup() {
        super.setup();
        this.dataCode = useRef('dataCode');
        this.dataCodeImport = useRef('dataCodeImport');
        console.log('this.dataCode');
    },

    async _onGenerate() {
        const dataCode = this.props.mode === 'generate'
            ? this.dataCode.el?.value || ''
            : this.dataCodeImport.el?.value || '';

        if (dataCode) {
            try {
                // Опитваме се да добавим свойството директно
                this.props.move.context.default_data_code = dataCode;
            } catch (error) {
                console.warn('We cannot modify the context directly:', error);
            }
        }
        super._onGenerate();
    }
});
