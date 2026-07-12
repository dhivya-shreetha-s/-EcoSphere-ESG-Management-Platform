/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { EsgScoreRing } from "./esg_score_ring";
import { EsgCategoryChart } from "./esg_category_chart";
import { EsgAlertCard } from "./esg_alert_card";
import { EsgAiChatPanel } from "./esg_ai_chat_panel";

export class EsgManagerDashboard extends Component {
    static template = "ecosphere.EsgManagerDashboard";
    static components = { EsgScoreRing, EsgCategoryChart, EsgAlertCard, EsgAiChatPanel };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            department: {},
            score: { score_overall: 0.0, score_env: 0.0, score_social: 0.0, score_gov: 0.0 },
            employees: [],
            alerts: [],
            headcount: 0,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        try {
            // Find department of current manager employee record
            const emps = await this.orm.searchRead(
                "hr.employee",
                [["user_id", "=", this.orm.user.userId]],
                ["department_id"]
            );

            if (emps.length > 0 && emps[0].department_id) {
                this.state.department = {
                    id: emps[0].department_id[0],
                    name: emps[0].department_id[1]
                };
                const deptId = this.state.department.id;

                // Load department score
                const scores = await this.orm.searchRead(
                    "esg.score",
                    [["scope", "=", "department"], ["department_id", "=", deptId]],
                    [],
                    { limit: 1, order: "period_start desc" }
                );
                if (scores.length > 0) {
                    this.state.score = scores[0];
                }

                // Load headcount
                this.state.headcount = await this.orm.searchCount(
                    "hr.employee",
                    [["department_id", "=", deptId]]
                );

                // Load department employees & scores
                const deptEmps = await this.orm.searchRead(
                    "hr.employee",
                    [["department_id", "=", deptId]],
                    ["name", "job_title"]
                );

                // For each employee, load their latest score
                const enrichedEmps = [];
                for (const emp of deptEmps) {
                    const empScores = await this.orm.searchRead(
                        "esg.score",
                        [["scope", "=", "employee"], ["employee_id", "=", emp.id]],
                        ["score_overall", "score_label"],
                        { limit: 1, order: "period_start desc" }
                    );
                    enrichedEmps.push({
                        id: emp.id,
                        name: emp.name,
                        job_title: emp.job_title || "Team Member",
                        score: empScores.length > 0 ? empScores[0].score_overall : 0.0,
                        tier: empScores.length > 0 ? empScores[0].score_label : "bronze"
                    });
                }
                this.state.employees = enrichedEmps;

                // Load department alerts
                this.state.alerts = await this.orm.searchRead(
                    "esg.alert",
                    [
                        ["target_role", "in", ["employee", "manager"]],
                        ["state", "!=", "resolved"],
                        "|",
                        ["scope", "=", "org"],
                        "&", ["scope", "=", "department"], ["department_id", "=", deptId]
                    ],
                    []
                );
            }
        } catch (e) {
            console.error("Failed to load Manager Dashboard data", e);
        }
    }
}
