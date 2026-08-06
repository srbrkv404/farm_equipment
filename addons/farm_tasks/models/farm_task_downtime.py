# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FarmTaskDowntime(models.Model):
    _name = 'farm.task.downtime'
    _description = 'Простой в ходе выполнения задания'
    _order = 'start_time'

    task_id = fields.Many2one('farm.task', string='Задание', required=True, ondelete='cascade')

    reason = fields.Selection([
        ('breakdown', 'Поломка техники'),
        ('break', 'Перерыв'),
        ('weather', 'Погодные условия'),
        ('fuel', 'Заправка'),
        ('other', 'Другое'),
    ], string='Причина', default='other', required=True)

    start_time = fields.Datetime(string='Начало простоя', required=True, default=fields.Datetime.now)
    end_time = fields.Datetime(string='Окончание простоя')

    duration = fields.Float(string='Длительность, ч', compute='_compute_duration', store=True, digits=(6, 2))

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = delta.total_seconds() / 3600.0
            else:
                rec.duration = 0.0
