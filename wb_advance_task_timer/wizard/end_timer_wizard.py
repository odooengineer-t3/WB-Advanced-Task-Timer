from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ProjectTaskEndWizard(models.TransientModel):
    _name = 'project.task.end.wizard'
    _description = 'Project Task End Wizard'

    task_timer_id = fields.Many2one('project.task.timer', string='Timer', required=True)
    task_description = fields.Text(string='Enter Task Description')
    
    start_date = fields.Datetime(
        string='Start Date',
        related='task_timer_id.start_time',  
        readonly=True
    )
    end_date = fields.Datetime(string='End Date', default=fields.Datetime.now, readonly=True)
    duration = fields.Char(string='Duration (HH:MM)', compute='_compute_duration')

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.end_date:
                diff = record.end_date - record.start_date
                total_seconds = int(diff.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                record.duration = f"{hours:02}:{minutes:02}"
            else:
                record.duration = "00:00"


    def action_end_task(self):
        self.ensure_one()
        
        self.end_date = fields.Datetime.now()
        
        
        try:
            res = self.task_timer_id.task_id.action_timer_stop()
            logger.info("ACTION TIMER STOP RESULT: %s", res)
            
            if res and isinstance(res, dict) and res.get('res_model') == 'hr.timesheet.stop.timer.confirmation.wizard':
                logger.info("Standard wizard detected. Attempting auto-confirmation.")
                ctx = res.get('context', {})
                wiz = self.env[res['res_model']].sudo().with_context(ctx).create({})
                
            
                confirmed = False
            
                target_methods = ['action_save_timesheet', 'action_confirm', 'save', 'confirm']
                
                for method in target_methods:
                    if hasattr(wiz, method):
                        try:
                            getattr(wiz, method)()
                            logger.info("Successfully executed wizard method: %s", method)
                            confirmed = True
                            break
                        except Exception as e:
                            logger.warning("Failed to execute wizard method %s: %s", method, e)
                
                if not confirmed:
                    logger.warning("Could not find suitable confirmation method on standard wizard.")
                
                if not confirmed:
                    logger.warning("Could not find confirmation method on standard wizard.")
                    
        except AttributeError:
            logger.warning("Standard action_timer_stop not found.")

       
        duration_seconds = (self.end_date - self.start_date).total_seconds()
        unit_amount = duration_seconds / 3600.0

        recent_timesheet = self.env['account.analytic.line'].search([
            ('task_id', '=', self.task_timer_id.task_id.id),
            ('user_id', '=', self.task_timer_id.user_id.id),
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=1)) # Created just now
        ], order='create_date desc', limit=1)

        if recent_timesheet:
            recent_timesheet.write({
                'name': self.task_description or '/',
                'unit_amount': unit_amount,
            })
            
          
            try:
                recent_timesheet.write({'timer_start': False})
            except Exception:
                pass
        else:
            
            self.env['account.analytic.line'].create({
                'name': self.task_description or '/',
                'project_id': self.task_timer_id.project_id.id,
                'task_id': self.task_timer_id.task_id.id,
                'date': fields.Date.context_today(self),
                'unit_amount': unit_amount,
                'user_id': self.task_timer_id.user_id.id,
                'employee_id': self.env['hr.employee'].search([('user_id', '=', self.task_timer_id.user_id.id)], limit=1).id,
            })
            
        
        potential_running_lines = self.env['account.analytic.line'].search([
            ('task_id', '=', self.task_timer_id.task_id.id),
            ('user_id', '=', self.task_timer_id.user_id.id),
            ('date', '>=', fields.Date.context_today(self) - timedelta(days=30)),
        ])
        
       
        
        timer_fields = ['timer_start', 'timer_pause']

        for line in potential_running_lines:
            for field_name in timer_fields:
                try:
                    if line[field_name]:
                        line.sudo().write({field_name: False})
                        logger.info("Force stopped timer by clearing field '%s' on line %s", field_name, line.id)
                except Exception as e:
                    logger.warning("Could not clear field '%s' on line %s: %s", field_name, line.id, e)
            
           
            if recent_timesheet and line.id == recent_timesheet.id:
                pass 
            elif line.unit_amount == 0 and unit_amount > 0:
                pass

        self.task_timer_id.write({
            'start_time': self.start_date,
            'end_date': self.end_date,
            'description': self.task_description,
            'is_running': False,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_view_timer',
        }
