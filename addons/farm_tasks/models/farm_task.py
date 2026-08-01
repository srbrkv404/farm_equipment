# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class FarmTask(models.Model):
    _name = 'farm.task'
    _description = 'Задание механизатору на поле'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date, planned_start'

    name = fields.Char(string='Название', compute='_compute_name', store=True)

    field_number = fields.Char(string='Номер поля', required=True, tracking=True)

    operation_type = fields.Selection([
        ('plowing', 'Вспашка'),
        ('sowing', 'Посев'),
        ('spraying', 'Опрыскивание'),
        ('harvesting', 'Уборка'),
        ('other', 'Другое'),
    ], string='Операция', required=True, default='plowing', tracking=True)

    area = fields.Float(string='Объём работ, га')

    date = fields.Date(string='Дата', required=True, default=fields.Date.context_today,
                        tracking=True)
    planned_start = fields.Datetime(string='Плановое начало')
    planned_end = fields.Datetime(string='Плановое завершение')

    actual_start = fields.Datetime(string='Фактическое начало', readonly=True)
    actual_end = fields.Datetime(string='Фактическое завершение', readonly=True)

    state = fields.Selection([
        ('waiting', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('done', 'Выполнена'),
    ], string='Статус', default='waiting', required=True, tracking=True)

    description = fields.Text(string='Полное описание')
    plowing_depth = fields.Float(string='Глубина вспашки, см')
    application_rate = fields.Float(string='Норма внесения')
    application_rate_uom = fields.Selection([
        ('kg_ha', 'кг/га'),
        ('l_ha', 'л/га'),
    ], string='Единица нормы внесения')
    field_features = fields.Text(string='Особенности поля')

    equipment_id = fields.Many2one('farm.equipment', string='Назначенная техника', tracking=True)
    driver_id = fields.Many2one('res.partner', string='Механизатор',
                                 domain=[('is_company', '=', False)], tracking=True)

    @api.depends('field_number', 'operation_type')
    def _compute_name(self):
        labels = dict(self._fields['operation_type'].selection)
        for rec in self:
            op = labels.get(rec.operation_type, '')
            rec.name = 'Поле %s — %s' % (rec.field_number or '?', op)

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        if self.equipment_id and self.equipment_id.driver_id:
            self.driver_id = self.equipment_id.driver_id

    def action_start(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError('Задача уже выполнена.')
            rec.write({
                'state': 'in_progress',
                'actual_start': fields.Datetime.now(),
            })

    def action_done(self):
        for rec in self:
            rec.write({
                'state': 'done',
                'actual_end': fields.Datetime.now(),
            })

    def action_reset_to_waiting(self):
        for rec in self:
            rec.write({
                'state': 'waiting',
                'actual_start': False,
                'actual_end': False,
            })
