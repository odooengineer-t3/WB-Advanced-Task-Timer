// /** @odoo-module **/

// import { registry } from "@web/core/registry";
// import { formView } from "@web/views/form/form_view";

// class TaskEndWizardTimer extends FormController {
//     setup() {
//         super.setup();
//         this._startTimer();
//     }

//     _startTimer() {
//         this.timer = setInterval(() => {
//             const now = luxon.DateTime.now().toISO();

//             this.model.root.update({
//                 end_date: now,
//             });
//         }, 1000);
//     }

//     destroy() {
//         if (this.timer) {
//             clearInterval(this.timer);
//         }
//         super.destroy();
//     }
// }

// registry.category("views").add("task_end_timer_wizard", {
//     ...formView,
//     Controller: TaskEndWizardTimer,
// });
