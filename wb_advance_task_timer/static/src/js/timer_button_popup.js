/** @odoo-module **/

import { Component, useState, onWillDestroy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TaskTimerSystray extends Component {
    static template = "wb_advance_task_timer.TimerButton";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.menuService = useService("menu");

        this.state = useState({
            isRunning: false,
            duration: 0,
            startTime: null,
            taskName: '',
            timerId: null,
            isVisible: false, // Default hidden until check
        });

        this.interval = null;
        this.visibilityInterval = null;
        onWillDestroy(() => {
            clearInterval(this.interval);
            clearInterval(this.visibilityInterval);
        });

        this._fetchRunningTimer();

        // Check visibility periodically
        this.visibilityInterval = setInterval(() => {
            this._checkVisibility();
        }, 500);
    }

    _checkVisibility() {
        // Always visible if running
        if (this.state.isRunning) {
            if (!this.state.isVisible) this.state.isVisible = true;
            return;
        }

        const currentApp = this.menuService.getCurrentApp();
        // Visible if in Project App
        // Check both ID and Name to be safe
        const isProject = currentApp && (currentApp.xmlid === 'project.menu_main_pm' || currentApp.name === 'Project');

        if (isProject) {
            if (!this.state.isVisible) this.state.isVisible = true;
        } else {
            if (this.state.isVisible) this.state.isVisible = false;
        }
    }

    async _fetchRunningTimer() {
        const result = await this.orm.call("project.task.timer", "action_get_running_timer", []);
        if (result.running) {
            this.state.isRunning = true;
            this.state.startTime = new Date(result.start_time + "Z");
            this.state.duration = result.duration;
            this.state.taskName = result.task_name;
            this.state.timerId = result.timer_id;
            this._startTimerInterval();
        } else {
            this.state.isRunning = false;
            this.state.duration = 0;
            clearInterval(this.interval);
        }
        // Initial visibility check after fetching status
        this._checkVisibility();
    }

    _startTimerInterval() {
        if (this.interval) clearInterval(this.interval);
        this.interval = setInterval(() => {
            if (this.state.startTime) {
                const now = new Date();
                const diff = Math.floor((now - this.state.startTime) / 1000);
                this.state.duration = diff > 0 ? diff : 0;
            } else {
                this.state.duration++;
            }
        }, 1000);
    }

    formatDuration(seconds) {
        const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
        const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${h}:${m}:${s}`;
    }

    async onClick() {
        if (this.state.isRunning) {

        } else {
            // Open Wizard
            const action = {
                type: 'ir.actions.act_window',
                res_model: 'project.task.timer.wizard',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            };

            // Standard action call
            await this.action.doAction(action, {
                onClose: () => {
                    this._fetchRunningTimer();
                }
            });
        }
    }

    async onStop() {
        if (!this.state.timerId) return;

        // Instant stop without wizard
        await this.orm.call("project.task.timer", "action_instant_stop", [this.state.timerId]);
        this._fetchRunningTimer();
    }
}

registry.category("systray").add(
    "wb_advance_task_timer.TaskTimerSystray",
    { Component: TaskTimerSystray },
    { sequence: 5 }
);
