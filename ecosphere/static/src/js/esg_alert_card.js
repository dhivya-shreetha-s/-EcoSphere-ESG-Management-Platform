/** @odoo-module **/
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class EsgAlertCard extends Component {
    static template = "ecosphere.EsgAlertCard";
    static props = {
        alert: { type: Object },
        onUpdate: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
    }

    get alertClass() {
        const severity = this.props.alert.severity || "warning";
        if (severity === "critical") return "esg-alert-critical border-danger bg-danger-light";
        if (severity === "warning") return "esg-alert-warning border-warning bg-warning-light";
        return "esg-alert-info border-info bg-info-light";
    }

    get severityBadgeClass() {
        const severity = this.props.alert.severity || "warning";
        if (severity === "critical") return "bg-danger text-white";
        if (severity === "warning") return "bg-warning text-dark";
        return "bg-info text-white";
    }

    async actionAcknowledge() {
        try {
            await this.orm.call("esg.alert", "action_acknowledge", [this.props.alert.id]);
            this.props.onUpdate();
        } catch (e) {
            console.error("Failed to acknowledge alert", e);
        }
    }

    async actionResolve() {
        try {
            await this.orm.call("esg.alert", "action_resolve", [this.props.alert.id]);
            this.props.onUpdate();
        } catch (e) {
            console.error("Failed to resolve alert", e);
        }
    }
}
