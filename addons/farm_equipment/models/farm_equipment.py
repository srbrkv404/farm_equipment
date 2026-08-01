# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class FarmEquipment(models.Model):
    _name = 'farm.equipment'
    _description = 'Сельхозтехника (трактор/комбайн)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Название', required=True, tracking=True)
    brand = fields.Char(string='Марка', tracking=True)

    equipment_type = fields.Selection([
        ('tractor', 'Трактор'),
        ('combine', 'Комбайн'),
        ('other', 'Другое'),
    ], string='Тип техники', default='tractor', required=True, tracking=True)

    working_width = fields.Float(string='Ширина захвата, м', digits=(6, 2))

    fuel_consumption = fields.Float(string='Норм. расход топлива', digits=(6, 2))
    fuel_consumption_uom = fields.Selection([
        ('l_per_ha', 'л/га'),
        ('l_per_hour', 'л/час'),
    ], string='Единица расхода', default='l_per_ha')

    driver_id = fields.Many2one(
        'res.partner', string='Механизатор (водитель)', tracking=True,
        domain=[('is_company', '=', False)],
        help='Сотрудник, за которым закреплена данная техника')

    state = fields.Selection([
        ('free', 'Свободна'),
        ('working', 'В работе'),
        ('maintenance', 'На обслуживании'),
    ], string='Статус', default='free', required=True, tracking=True)

    engine_hours = fields.Float(
        string='Моточасы (всего)', compute='_compute_totals', store=True)
    mileage = fields.Float(
        string='Пробег, км (всего)', compute='_compute_totals', store=True)
    avg_productivity = fields.Float(
        string='Средняя производительность, га/час',
        compute='_compute_totals', store=True)
    avg_fuel_per_ha = fields.Float(
        string='Средний факт. расход, л/га',
        compute='_compute_totals', store=True)

    log_ids = fields.One2many(
        'farm.equipment.log', 'equipment_id', string='Журнал работы')
    log_count = fields.Integer(string='Смен всего', compute='_compute_totals')

    active_log_id = fields.Many2one(
        'farm.equipment.log', string='Текущая смена',
        compute='_compute_active_log')

    @api.depends('log_ids.engine_hours_used', 'log_ids.mileage_used',
                 'log_ids.area_processed', 'log_ids.fuel_used', 'log_ids.state')
    def _compute_totals(self):
        for rec in self:
            done_logs = rec.log_ids.filtered(lambda l: l.state == 'done')
            total_hours = sum(done_logs.mapped('engine_hours_used'))
            total_area = sum(done_logs.mapped('area_processed'))
            total_fuel = sum(done_logs.mapped('fuel_used'))

            rec.engine_hours = total_hours
            rec.mileage = sum(done_logs.mapped('mileage_used'))
            rec.avg_productivity = (total_area / total_hours) if total_hours else 0.0
            rec.avg_fuel_per_ha = (total_fuel / total_area) if total_area else 0.0
            rec.log_count = len(done_logs)

    @api.depends('log_ids.state')
    def _compute_active_log(self):
        for rec in self:
            active = rec.log_ids.filtered(lambda l: l.state == 'in_progress')
            rec.active_log_id = active[:1]

    def action_start_work(self):
        """Начать работу: создать новую смену и перевести технику в 'в работе'."""
        self.ensure_one()
        if self.state == 'working':
            raise UserError('Эта техника уже в работе.')
        if self.state == 'maintenance':
            raise UserError('Техника на обслуживании, начать работу нельзя.')
        if not self.driver_id:
            raise UserError('Сначала назначьте механизатора для этой техники.')

        log = self.env['farm.equipment.log'].create({
            'equipment_id': self.id,
            'driver_id': self.driver_id.id,
            'date_start': fields.Datetime.now(),
            'engine_hours_start': self.engine_hours,
            'mileage_start': self.mileage,
            'state': 'in_progress',
        })
        self.state = 'working'

        return {
            'type': 'ir.actions.act_window',
            'name': 'Текущая смена',
            'res_model': 'farm.equipment.log',
            'view_mode': 'form',
            'res_id': log.id,
            'target': 'current',
        }

    def action_set_maintenance(self):
        for rec in self:
            if rec.state == 'working':
                raise UserError('Нельзя отправить на обслуживание технику, которая в работе.')
            rec.state = 'maintenance'

    def action_set_free(self):
        for rec in self:
            rec.state = 'free'

    def action_open_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Журнал работы: %s' % self.name,
            'res_model': 'farm.equipment.log',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id, 'default_driver_id': self.driver_id.id},
        }
