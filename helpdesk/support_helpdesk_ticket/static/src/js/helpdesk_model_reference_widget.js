/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ReferenceField } from "@web/views/fields/reference/reference_field";

/**
 * Task 8.2: Model Selection Widget
 *
 * This is a thin wrapper over Odoo's standard Reference field:
 * - Keeps the familiar UX (model dropdown + record many2one with search)
 * - Uses server-side selection filtering (models user can read)
 */
export class HelpdeskModelReferenceField extends ReferenceField {}

registry.category("fields").add("helpdesk_model_reference", {
    ...registry.category("fields").get("reference"),
    component: HelpdeskModelReferenceField,
});

