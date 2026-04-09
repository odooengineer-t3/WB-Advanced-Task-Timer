from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)    

class ProjectTask(models.Model):
    _inherit = 'project.task'
    _description = 'Project Task'   

    timer_ids = fields.One2many('project.task.timer', 'task_id', string='Timers')

    wb_timer_start = fields.Datetime(
        compute="_compute_wb_timer_start",
        string="Timer Start Time"
    )

    wb_is_timer_running = fields.Boolean(
        compute="_compute_wb_is_timer_running"
    )

    wb_timer_start_iso = fields.Char(
        compute="_compute_wb_timer_start_iso",
        string="Timer Start ISO"
    )

    @api.depends('timer_ids.is_running', 'timer_ids.user_id')
    def _compute_wb_timer_start(self):
        """Fetch the start time from the running timer for this task and user."""
        for task in self:
            timer = task.timer_ids.filtered(lambda t: t.user_id == self.env.user and t.is_running)
            task.wb_timer_start = timer.start_time if timer else False

    @api.depends('wb_timer_start')
    def _compute_wb_timer_start_iso(self):
        for task in self:
            task.wb_timer_start_iso = fields.Datetime.to_string(task.wb_timer_start) if task.wb_timer_start else False

    @api.depends('timer_ids.is_running', 'timer_ids.user_id')
    def _compute_wb_is_timer_running(self):
        for task in self:
            task.wb_is_timer_running = bool(
                task.timer_ids.filtered(lambda t: t.user_id == self.env.user and t.is_running)
            )

    def action_timer_start(self):
        """Start a timer for the current task."""
        self.ensure_one()

        super().action_timer_start()
        
        Timer = self.env['project.task.timer']
        running_timer = Timer.search([
            ('user_id', '=', self.env.user.id),
            ('is_running', '=', True)
        ], limit=1)
        
        if running_timer:
            raise UserError(f"You already have a running task: {running_timer.task_id.name}. Please stop it first.")
        
        
        Timer.create({
            'user_id': self.env.user.id,
            'task_id': self.id,
            'project_id': self.project_id.id,
            'start_time': fields.Datetime.now(),
            'is_running': True,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_view_timer',
        }

    def action_timer_stop(self):
        """Stop the standard timer and our custom timer."""
        Timer = self.env['project.task.timer']
        running_timers = Timer.search([
            ('user_id', '=', self.env.user.id),
            ('task_id', '=', self.id),
            ('is_running', '=', True)
        ])
       
        running_timers.write({
            'is_running': False,
            'end_date': fields.Datetime.now()
        })
        
        #
        try:
            return super().action_timer_stop()
        except AttributeError:
            return True
    

    def action_open_end_timer_wizard(self):
        print("open end timer wizard....................................")  
        self.ensure_one()

        timer = self.env['project.task.timer'].search([
            ('user_id', '=', self.env.user.id),
            ('is_running', '=', True),
            ('task_id', '=', self.id)
        ], limit=1)

        if not timer:
            logger.warning('No running timer found for task %s', self.id)   
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
            'params': {
                'title': 'No Running Timer',
                'message': 'No running timer found for this task.',
                'type': 'warning',
            }
        }

        return {
        'name': 'End Task',
        'type': 'ir.actions.act_window',
        'res_model': 'project.task.end.wizard',
        'view_mode': 'form',
        'views': [(False, 'form')],
        'target': 'new',
        'context': {
            'default_task_timer_id': timer.id,
        }
}
    def get_running_timer(self):
        self.ensure_one()
        timer = self.env['project.task.timer'].search([
            ('task_id', '=', self.id),
            ('user_id', '=', self.env.user.id),
            ('is_running', '=', True)
        ], limit=1)

        return {'start_time': timer.start_time if timer else False}

   
class ProjectTaskTimer(models.Model):
    _name = 'project.task.timer'
    _description = 'Project Task Timer'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )
    project_id = fields.Many2one('project.project', string='Project')
    task_id= fields.Many2one('project.task', string='Task')
    start_time = fields.Datetime()
    is_running = fields.Boolean(default=False)
    description = fields.Text(string="Task Description") 
    end_date = fields.Datetime(string='End Date')

    @api.model
    def action_toggle_timer(self):
        timer = self.search([
            ('user_id', '=', self.env.user.id),
            ('is_running', '=', True)
        ], limit=1)

        if timer:
            timer.write({
                'is_running': False,
            })
            return {'running': False}
        else:
            return {'running': True}

    @api.model
    def action_get_running_timer(self):
        timer = self.search([
            ('user_id', '=', self.env.user.id),
            ('is_running', '=', True)
        ], limit=1)
        if timer:
            duration = (fields.Datetime.now() - timer.start_time).total_seconds()
            return {
                'running': True,
                'duration': int(duration),
                'start_time': timer.start_time,
                'task_name': timer.task_id.name or 'Unknown Task',
                'timer_id': timer.id,
            }
        return {'running': False, 'duration': 0}

    def action_instant_stop(self):
        """Stop the timer immediately and log time without popup."""
        self.ensure_one()
        
        # Calculate end values
        end_date = fields.Datetime.now()
        duration_seconds = (end_date - self.start_time).total_seconds()
        unit_amount = duration_seconds / 3600.0
        
        # Stop standard Odoo timer and handle any wizards
        try:
            res = self.task_id.action_timer_stop()
            # If it returns a wizard (confirmation), try to auto-confirm it
            if res and isinstance(res, dict) and res.get('res_model') == 'hr.timesheet.stop.timer.confirmation.wizard':
                ctx = res.get('context', {})
                wiz = self.env[res['res_model']].sudo().with_context(ctx).create({})
                
                # Try standard confirmation methods
                for method in ['action_save_timesheet', 'action_confirm', 'save', 'confirm']:
                    if hasattr(wiz, method):
                        try:
                            getattr(wiz, method)()
                            break
                        except Exception:
                            continue
        except AttributeError:
            pass # Standard timer might not be there

        # Update or Create Timesheet
        # Find if standard timer created one recently (last 1 min)
        from datetime import timedelta
        recent_timesheet = self.env['account.analytic.line'].search([
            ('task_id', '=', self.task_id.id),
            ('user_id', '=', self.user_id.id),
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=1))
        ], order='create_date desc', limit=1)

        if recent_timesheet:
            # Update existing
            recent_timesheet.write({
                'unit_amount': unit_amount, 
            })
            # Ensure timer state is cleared
            try:
                recent_timesheet.write({'timer_start': False})
            except Exception:
                pass
        else:
            # Create new
            self.env['account.analytic.line'].create({
                'name': '/', # Default description
                'project_id': self.project_id.id,
                'task_id': self.task_id.id,
                'date': fields.Date.context_today(self),
                'unit_amount': unit_amount,
                'user_id': self.user_id.id,
                'employee_id': self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1).id,
            })

        # Final cleanup of any stuck timer fields on timesheets
        potential_running_lines = self.env['account.analytic.line'].search([
            ('task_id', '=', self.task_id.id),
            ('user_id', '=', self.user_id.id),
            ('date', '>=', fields.Date.context_today(self) - timedelta(days=30)),
        ])
        for line in potential_running_lines:
             if hasattr(line, 'timer_start') and line.timer_start:
                 try: line.sudo().write({'timer_start': False})
                 except: pass

        # Mark custom timer as stopped
        self.write({
            'is_running': False,
            'end_date': end_date,
        })

        return {'running': False}