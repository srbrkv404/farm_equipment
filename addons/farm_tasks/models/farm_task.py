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

    start_latitude = fields.Float(string='Широта (старт)', digits=(10, 6), readonly=True)
    start_longitude = fields.Float(string='Долгота (старт)', digits=(10, 6), readonly=True)
    end_latitude = fields.Float(string='Широта (финиш)', digits=(10, 6), readonly=True)
    end_longitude = fields.Float(string='Долгота (финиш)', digits=(10, 6), readonly=True)

    state = fields.Selection([
        ('waiting', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('paused', 'Простой'),
        ('done', 'Выполнена'),
    ], string='Статус', default='waiting', required=True, tracking=True)

    downtime_ids = fields.One2many('farm.task.downtime', 'task_id', string='Простои')
    downtime_hours = fields.Float(
        string='Простой, ч', compute='_compute_downtime_hours', store=True, digits=(6, 2))

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

    @api.depends('downtime_ids.duration')
    def _compute_downtime_hours(self):
        for rec in self:
            rec.downtime_hours = sum(rec.downtime_ids.mapped('duration'))

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

    def action_pause(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError('Приостановить можно только задание, которое сейчас в работе.')
            rec.env['farm.task.downtime'].create({
                'task_id': rec.id,
                'start_time': fields.Datetime.now(),
            })
            rec.state = 'paused'

    def action_resume(self):
        for rec in self:
            if rec.state != 'paused':
                raise UserError('Возобновить можно только приостановленное задание.')
            open_downtime = rec.downtime_ids.filtered(lambda d: not d.end_time)[:1]
            if open_downtime:
                open_downtime.end_time = fields.Datetime.now()
            rec.state = 'in_progress'

    def action_done(self):
        for rec in self:
            if rec.state not in ('in_progress', 'paused'):
                raise UserError('Завершить можно только задание, которое в работе или на простое.')
            open_downtime = rec.downtime_ids.filtered(lambda d: not d.end_time)[:1]
            if open_downtime:
                open_downtime.end_time = fields.Datetime.now()
            rec.write({
                'state': 'done',
                'actual_end': fields.Datetime.now(),
            })

    def action_reset_to_waiting(self):
        for rec in self:
            rec.downtime_ids.unlink()
            rec.write({
                'state': 'waiting',
                'actual_start': False,
                'actual_end': False,
                'start_latitude': 0.0,
                'start_longitude': 0.0,
                'end_latitude': 0.0,
                'end_longitude': 0.0,
            })
