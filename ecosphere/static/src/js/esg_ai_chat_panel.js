/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class EsgAiChatPanel extends Component {
    static template = "ecosphere.EsgAiChatPanel";
    static props = {
        role: { type: String, optional: true },
    };

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            open: false,
            message: "",
            history: [
                {
                    role: "assistant",
                    content: "Hi! I am your EcoSphere AI Assistant. How can I help you with your ESG sustainability goals today?"
                }
            ],
            loading: false,
        });

        this.suggestionChips = [
            "How can I improve my ESG score?",
            "What are my pending action items?",
            "Analyze my environmental footprint.",
        ];
    }

    toggleOpen() {
        this.state.open = !this.state.open;
    }

    async sendMessage(text) {
        const msgText = text || this.state.message;
        if (!msgText.strip) return;
        const msg = msgText.trim();
        if (!msg) return;

        // Push user message
        this.state.history.push({ role: "user", content: msg });
        this.state.message = "";
        this.state.loading = true;

        try {
            const data = await this.rpc("/ecosphere/ai/chat", {
                message: msg,
                conversation_history: this.state.history.map(h => ({
                    role: h.role,
                    content: h.content
                }))
            });

            this.state.history.push({
                role: "assistant",
                content: data.response || "No response received."
            });
        } catch (e) {
            console.error("AI chat failed", e);
            this.state.history.push({
                role: "assistant",
                content: "I encountered an error connecting to the Grok server. Please verify your network connection."
            });
        } finally {
            this.state.loading = false;
        }
    }
}
EsgAiChatPanel.defaultProps = {
    role: "employee",
};
