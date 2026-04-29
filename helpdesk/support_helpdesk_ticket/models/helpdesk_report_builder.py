# -- coding: utf-8 --
##############################################################################
#                                                                            #
# Part of WebbyCrown Solutions (Website: www.webbycrown.com).                #
# Copyright © 2025 WebbyCrown Solutions. All Rights Reserved.                #
#                                                                            #
# This module is developed and maintained by WebbyCrown Solutions.           #
# Unauthorized copying of this file, via any medium, is strictly prohibited. #
# Licensed under the terms of the WebbyCrown Solutions License Agreement.    #
#                                                                            #
##############################################################################

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from datetime import datetime


class HelpdeskReportTemplate(models.Model):
    _name = 'helpdesk.report.template'
    _description = 'Helpdesk Custom Report Template'

    name = fields.Char(
        string='Report Name',
        required=True,
        help='Name of the custom report'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Target model is fixed to helpdesk.ticket for this task
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        default=lambda self: self.env.ref('support_helpdesk_ticket.model_helpdesk_ticket', raise_if_not_found=False),
        readonly=True
    )

    view_type = fields.Selection(
        [
            ('tree', 'List'),
            ('pivot', 'Pivot'),
            ('graph', 'Chart'),
        ],
        string='View Type',
        default='pivot',
        required=True,
        help='Default view to open for this report'
    )

    graph_type = fields.Selection(
        [
            ('status', 'By Status'),
            ('priority', 'By Priority'),
            ('channel', 'By Channel'),
            ('timeline', 'Timeline'),
        ],
        string='Chart Type',
        default='status',
        help='Which predefined chart to use when opening in chart view'
    )

    group_by_field = fields.Selection(
        [
            ('state', 'Status'),
            ('priority', 'Priority'),
            ('team_id', 'Team'),
            ('user_id', 'Assigned To'),
            ('ticket_type_id', 'Type'),
            ('category_id', 'Category'),
            ('channel', 'Channel'),
            ('create_date:day', 'Creation Day'),
            ('create_date:month', 'Creation Month'),
        ],
        string='Primary Group By',
        default='state',
        help='Main field to group results by'
    )

    secondary_group_by_field = fields.Selection(
        [
            ('team_id', 'Team'),
            ('user_id', 'Assigned To'),
            ('ticket_type_id', 'Type'),
            ('category_id', 'Category'),
            ('channel', 'Channel'),
        ],
        string='Secondary Group By',
        help='Optional second field to group results by'
    )

    measure_field = fields.Selection(
        [
            ('id', 'Ticket Count'),
            ('days_to_resolve', 'Days to Resolve'),
        ],
        string='Measure',
        default='id',
        help='Measure used in pivot/chart views'
    )

    date_from = fields.Date(
        string='From Date',
        help='Only include tickets created on or after this date'
    )
    date_to = fields.Date(
        string='To Date',
        help='Only include tickets created on or before this date'
    )

    domain = fields.Char(
        string='Advanced Domain',
        help='Optional Odoo domain expression for additional filtering, e.g. '
             "[('priority', '=', '2'), ('state', '!=', 'cancelled')]"
    )

    def action_open_report(self):
        """Open the configured report on helpdesk tickets."""
        self.ensure_one()

        # Base action configuration
        action = {
            'name': self.name or _('Custom Helpdesk Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'target': 'current',
        }

        # Select base view and view_mode according to view_type / graph_type
        if self.view_type == 'tree':
            action['view_mode'] = 'tree,form'
            action['view_id'] = self.env.ref(
                'support_helpdesk_ticket.view_helpdesk_ticket_tree'
            ).id
        elif self.view_type == 'pivot':
            action['view_mode'] = 'pivot,graph'
            action['view_id'] = self.env.ref(
                'support_helpdesk_ticket.view_helpdesk_ticket_pivot'
            ).id
        else:  # graph
            action['view_mode'] = 'graph,pivot'
            if self.graph_type == 'priority':
                graph_view = self.env.ref(
                    'support_helpdesk_ticket.view_helpdesk_ticket_graph_priority'
                )
            elif self.graph_type == 'channel':
                graph_view = self.env.ref(
                    'support_helpdesk_ticket.view_helpdesk_ticket_graph_channel'
                )
            elif self.graph_type == 'timeline':
                graph_view = self.env.ref(
                    'support_helpdesk_ticket.view_helpdesk_ticket_graph_timeline'
                )
            else:  # status
                graph_view = self.env.ref(
                    'support_helpdesk_ticket.view_helpdesk_ticket_graph'
                )
            action['view_id'] = graph_view.id

        # Build domain: date range + advanced domain
        domain = []
        if self.date_from:
            domain.append(('create_date', '>=', datetime.combine(self.date_from, datetime.min.time())))
        if self.date_to:
            domain.append(('create_date', '<=', datetime.combine(self.date_to, datetime.max.time())))

        if self.domain:
            try:
                extra_domain = safe_eval(self.domain)
                if isinstance(extra_domain, (list, tuple)):
                    domain += extra_domain
            except Exception:
                # Fail silently on invalid domain, keep basic filters
                pass

        if domain:
            action['domain'] = domain

        # Context for group_by and measure
        ctx = dict(self.env.context or {})
        if self.group_by_field:
            ctx['group_by'] = self.group_by_field
        if self.secondary_group_by_field:
            ctx.setdefault('group_by', [])
            # allow multiple group by fields when supported
            if isinstance(ctx['group_by'], list):
                ctx['group_by'].append(self.secondary_group_by_field)
        if self.measure_field and self.measure_field != 'id':
            ctx['measure'] = self.measure_field

        action['context'] = ctx
        return action

