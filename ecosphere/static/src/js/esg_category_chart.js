/** @odoo-module **/
import { Component } from "@odoo/owl";

export class EsgCategoryChart extends Component {
    static template = "ecosphere.EsgCategoryChart";
    static props = {
        envScore: { type: Number, optional: true },
        socialScore: { type: Number, optional: true },
        govScore: { type: Number, optional: true },
    };
}
EsgCategoryChart.defaultProps = {
    envScore: 0,
    socialScore: 0,
    govScore: 0,
};
