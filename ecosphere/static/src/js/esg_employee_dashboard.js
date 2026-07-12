/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { EsgScoreRing } from "./esg_score_ring";
import { EsgCategoryChart } from "./esg_category_chart";
import { EsgAiChatPanel } from "./esg_ai_chat_panel";

export class EsgEmployeeDashboard extends Component {
    static template = "ecosphere.EsgEmployeeDashboard";
    static components = { EsgScoreRing, EsgCategoryChart, EsgAiChatPanel };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            employee: {},
            score: { score_overall: 0.0, score_env: 0.0, score_social: 0.0, score_gov: 0.0 },
            recommendations: [],
            events: [],
            xp: 0,
            streak: 0,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        try {
            // Load employee information linked to current user
            const emps = await this.orm.searchRead(
                "hr.employee",
                [["user_id", "=", this.orm.user.userId]],
                ["name", "department_id", "job_title", "parent_id"]
            );

            if (emps.length > 0) {
                this.state.employee = emps[0];
                const empId = emps[0].id;

                // Run onboarding check/create default goal
                await this.orm.call("esg.goal", "check_or_create_onboarding_goal", [empId]);

                // Fetch latest score
                const scores = await this.orm.searchRead(
                    "esg.score",
                    [["scope", "=", "employee"], ["employee_id", "=", empId]],
                    [],
                    { limit: 1, order: "period_start desc" }
                );
                if (scores.length > 0) {
                    this.state.score = scores[0];
                }

                // Fetch action items
                this.state.recommendations = await this.orm.searchRead(
                    "esg.recommendation",
                    [["scope", "=", "employee"], ["employee_id", "=", empId], ["state", "=", "open"]],
                    []
                );

                // Fetch volunteer events
                this.state.events = await this.env.services.orm.searchRead(
                    "esg.csr.event",
                    [["state", "in", ["draft", "approved"]]],
                    []
                );

                // Fetch cumulative XP ledger sum
                const xps = await this.orm.readGroup(
                    "esg.xp.ledger",
                    [["employee_id", "=", empId]],
                    ["delta_xp:sum"],
                    []
                );
                this.state.xp = xps[0] ? xps[0].delta_xp : 0;
            }
        } catch (e) {
            console.error("Failed to load Employee Dashboard data", e);
        }
    }

    async markActionDone(recId) {
        try {
            await this.orm.write("esg.recommendation", [recId], { state: "done" });
            await this.loadData();
        } catch (e) {
            console.error("Failed to mark action done", e);
        }
    }

    async registerEvent(eventId) {
        try {
            await this.orm.create("esg.csr.event.registration", [{
                event_id: eventId,
                employee_id: this.state.employee.id,
                state: "registered"
            }]);
            await this.loadData();
        } catch (e) {
            console.error("Failed to register for event", e);
        }
    }
}
