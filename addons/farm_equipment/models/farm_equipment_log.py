# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class FarmEquipmentLog(models.Model):
    _name = 'farm.equipment.log'
    _description = 'Журнал использования техники (смена/выезд в поле)'
    _order = 'date_start desc'

    equipment_id = fields.Many2one(
        'farm.equipment', string='Техника', required=True, ondelete='cascade')
    driver_id = fields.Many2one(
        'res.partner', string='Механизатор', required=True)

    date_start = fields.Datetime(string='Начало работы', required=True,
                                  default=fields.Datetime.now)
    date_end = fields.Datetime(string='Окончание работы')

    engine_hours_start = fields.Float(string='Моточасы на начало смены')
    engine_hours_end = fields.Float(string='Моточасы на конец смены')
    engine_hours_used = fields.Float(
        string='Наработано моточасов', compute='_compute_used', store=True)

    mileage_start = fields.Float(string='Пробег на начало, км')
    mileage_end = fields.Float(string='Пробег на конец, км')
    mileage_used = fields.Float(
        string='Пройдено, км', compute='_compute_used', store=True)

    area_processed = fields.Float(string='Обработано площади, га')
    fuel_used = fields.Float(string='Израсходовано топлива, л')

    productivity = fields.Float(
        string='Производительность, га/час', compute='_compute_used', store=True)
    fuel_per_ha = fields.Float(
        string='Факт. расход, л/га', compute='_compute_used', store=True)

    state = fields.Selection([
        ('in_progress', 'В работе'),
        ('done', 'Завершено'),
    ], default='in_progress', string='Статус смены', required=True)

    notes = fields.Text(string='Примечания')

    @api.depends('engine_hours_start', 'engine_hours_end',
                 'mileage_start', 'mileage_end',
                 'area_processed', 'fuel_used')
    def _compute_used(self):
        for rec in self:
            rec.engine_hours_used = max(rec.engine_hours_end - rec.engine_hours_start, 0.0)
            rec.mileage_used = max(rec.mileage_end - rec.mileage_start, 0.0)
            rec.productivity = (
                rec.area_processed / rec.engine_hours_used
                if rec.engine_hours_used else 0.0
            )
            rec.fuel_per_ha = (
                rec.fuel_used / rec.area_processed
                if rec.area_processed else 0.0
            )

    def action_finish(self):
        """Завершить смену: зафиксировать данные и освободить технику."""
        for rec in self:
            if rec.state == 'done':
                continue
            if rec.engine_hours_end < rec.engine_hours_start:
                raise UserError(
                    'Моточасы на конец смены не могут быть меньше, чем на начало.')
            if rec.mileage_end < rec.mileage_start:
                raise UserError(
                    'Пробег на конец смены не может быть меньше, чем на начало.')
            rec.date_end = fields.Datetime.now()
            rec.state = 'done'
            rec.equipment_id.state = 'free'
