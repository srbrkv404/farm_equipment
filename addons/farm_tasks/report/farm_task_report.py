# -*- coding: utf-8 -*-
from odoo import models


class FarmTaskMonthlyReport(models.AbstractModel):
    _name = 'report.farm_tasks.report_farm_task_monthly_document'
    _description = 'Отчёт по заданиям механизаторов за период'

    def _get_report_values(self, docids, data=None):
        tasks = self.env['farm.task'].browse(docids).sorted('date')
        operation_labels = dict(tasks._fields['operation_type'].selection)

        summary_by_operation = {}
        for task in tasks:
            row = summary_by_operation.setdefault(task.operation_type, {
                'label': operation_labels.get(task.operation_type, task.operation_type),
                'count': 0,
                'area': 0.0,
            })
            row['count'] += 1
            row['area'] += task.area

        return {
            'doc_ids': docids,
            'doc_model': 'farm.task',
            'docs': tasks,
            'operation_labels': operation_labels,
            'summary_by_operation': list(summary_by_operation.values()),
            'total_area': sum(tasks.mapped('area')),
            'total_downtime': sum(tasks.mapped('downtime_hours')),
            'date_from': min(tasks.mapped('date')) if tasks else False,
            'date_to': max(tasks.mapped('date')) if tasks else False,
        }
