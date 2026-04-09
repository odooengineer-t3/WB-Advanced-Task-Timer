/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");

        onMounted(() => {
            this.startTimerUpdates();
        });

        onWillUnmount(() => {
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
            }
        });
    },

    startTimerUpdates() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        this.updateTimers();
        this.timerInterval = setInterval(() => this.updateTimers(), 1000);
    },

    async updateTimers() {
        const timerElements = document.querySelectorAll(".o_task_live_timer");

        for (const el of timerElements) {
            const startTime = el.dataset.start;

            // If we have start time from the data attribute, calculate locally (no RPC needed)
            if (startTime) {
                // Ensure ISO format: replace space with T and append Z for UTC
                const isoStart = startTime.replace(" ", "T") + "Z";
                const start = new Date(isoStart);
                const now = new Date();
                const diff = Math.floor((now - start) / 1000);

                if (diff >= 0 && !isNaN(diff)) {
                    const h = String(Math.floor(diff / 3600)).padStart(2, "0");
                    const m = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
                    const s = String(diff % 60).padStart(2, "0");
                    el.textContent = `${h}:${m}:${s}`;
                }
                continue;
            }

            // Fallback: fetch timer from server using task ID
            const taskId = el.dataset.taskId;
            if (!taskId) continue;

            try {
                const res = await this.orm.call(
                    "project.task",
                    "get_running_timer",
                    [[parseInt(taskId)]]
                );

                if (!res || !res.start_time) {
                    el.textContent = "00:00:00";
                    continue;
                }

                // Ensure ISO format for RPC result too
                const isoStart = res.start_time.replace(" ", "T") + "Z";
                const start = new Date(isoStart);
                const now = new Date();
                const diff = Math.floor((now - start) / 1000);

                const h = String(Math.floor(diff / 3600)).padStart(2, "0");
                const m = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
                const s = String(diff % 60).padStart(2, "0");

                el.textContent = `${h}:${m}:${s}`;
            } catch (error) {
                console.error("Timer update error:", error);
            }
        }
    }
});

// Register the custom action to reload the page
registry.category("actions").add("reload_view_timer", () => {
    window.location.reload();
});