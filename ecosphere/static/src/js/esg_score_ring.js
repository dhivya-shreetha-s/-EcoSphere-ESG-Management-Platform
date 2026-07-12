/** @odoo-module **/
import { Component } from "@odoo/owl";

export class EsgScoreRing extends Component {
    static template = "ecosphere.EsgScoreRing";
    static props = {
        score: { type: Number, optional: true },
        label: { type: String, optional: true },
    };

    get strokeDashOffset() {
        const score = this.props.score || 0;
        const circumference = 2 * Math.PI * 40; // radius = 40
        return circumference - (score / 100) * circumference;
    }

    get scoreColorClass() {
        const score = this.props.score || 0;
        if (score >= 90) return "platinum";
        if (score >= 70) return "gold";
        if (score >= 50) return "silver";
        return "bronze";
    }

    get tierLabel() {
        const score = this.props.score || 0;
        if (score >= 90) return "Platinum";
        if (score >= 70) return "Gold";
        if (score >= 50) return "Silver";
        return "Bronze";
    }
}
EsgScoreRing.defaultProps = {
    score: 0,
    label: "Overall Score",
};
