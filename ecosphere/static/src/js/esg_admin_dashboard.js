/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { EsgScoreRing } from "./esg_score_ring";
import { EsgCategoryChart } from "./esg_category_chart";
import { EsgAlertCard } from "./esg_alert_card";
import { EsgAiChatPanel } from "./esg_ai_chat_panel";

export class EsgAdminDashboard extends Component {
    static template = "ecosphere.EsgAdminDashboard";
    static components = { EsgScoreRing, EsgCategoryChart, EsgAlertCard, EsgAiChatPanel };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            score: { score_overall: 0.0, score_env: 0.0, score_social: 0.0, score_gov: 0.0 },
            categories: [],
            alerts: [],
            totalEmissions: 1248.0,
            activeManagers: 42,
            complianceRate: 96.8,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        try {
            // Load org score
            const scores = await this.orm.searchRead(
                "esg.score",
                [["scope", "=", "org"]],
                [],
                { limit: 1, order: "period_start desc" }
            );
            if (scores.length > 0) {
                this.state.score = scores[0];
            }

            // Load categories and weights
            this.state.categories = await this.orm.searchRead(
                "esg.category",
                [],
                ["name", "code", "weight"],
                { order: "sequence" }
            );

            // Load all unresolved alerts
            this.state.alerts = await this.orm.searchRead(
                "esg.alert",
                [["state", "!=", "resolved"]],
                []
            );
        } catch (e) {
            console.error("Failed to load Admin Dashboard data", e);
        }
    }

    async updateWeights() {
        try {
            // Write each category weight to database
            for (const cat of this.state.categories) {
                await this.orm.write("esg.category", [cat.id], { weight: cat.weight });
            }
            
            // Recompute latest org score record to show live adjustment
            if (this.state.score.id) {
                await this.orm.call("esg.score", "action_compute_score", [this.state.score.id]);
            }
            await this.loadData();
        } catch (e) {
            console.error("Failed to update weights", e);
        }
    }

    onSliderChange(catId, val) {
        const cat = this.state.categories.find(c => c.id === catId);
        if (cat) {
            cat.weight = parseFloat(val);
        }
    }
}
