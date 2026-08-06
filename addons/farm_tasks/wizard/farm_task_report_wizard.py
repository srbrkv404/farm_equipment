# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError


class FarmTaskReportWizard(models.TransientModel):
    _name = 'farm.task.report.wizard'
    _description = 'Отчёт по заданиям за период'

    date_from = fields.Date(
        string='С', required=True,
        default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='По', required=True, default=fields.Date.today)
    driver_id = fields.Many2one(
        'res.partner', string='Механизатор',
        domain=[('is_company', '=', False)])

    def action_generate_report(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError('Дата "С" не может быть позже даты "По".')

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'done'),
        ]
        if self.driver_id:
            domain.append(('driver_id', '=', self.driver_id.id))

        tasks = self.env['farm.task'].search(domain)
        if not tasks:
            raise UserError('За выбранный период нет выполненных заданий.')

        return self.env.ref('farm_tasks.action_report_farm_task_monthly').report_action(tasks)
