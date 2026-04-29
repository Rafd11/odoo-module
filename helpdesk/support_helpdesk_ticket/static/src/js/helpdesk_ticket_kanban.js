/** @odoo-module **/

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KanbanController } from "@web/views/kanban/kanban_controller";

export class HelpdeskTicketKanbanController extends KanbanController {
    /**
     * Handle drag and drop assignment between columns grouped by user.
     */
    async onGroupChanged(ev) {
        const { group, record } = ev.detail || {};
        const newUserId = group?.value;
        const ticketId = record?.resId;

        if (newUserId && ticketId) {
            await this.env.services.orm.write("helpdesk.ticket", [ticketId], {
                user_id: newUserId,
                state: "assigned",
                assigned_date: new Date(),
            });
        }

        return super.onGroupChanged(ev);
    }
}

export const helpdeskTicketKanbanView = {
    ...kanbanView,
    Controller: HelpdeskTicketKanbanController,
};

registry.category("views").add("helpdesk_ticket_kanban", helpdeskTicketKanbanView);
