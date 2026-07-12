/** @odoo-module **/
/**
 * EcoSphere root client action registration.
 * Maps dashboard components to standard Odoo action tags.
 */
import { registry } from "@web/core/registry";
import { EsgEmployeeDashboard } from "./esg_employee_dashboard";
import { EsgManagerDashboard } from "./esg_manager_dashboard";
import { EsgAdminDashboard } from "./esg_admin_dashboard";

// Register Client Actions in the action registry
registry.category("actions").add("ecosphere.action_employee_dashboard", EsgEmployeeDashboard);
registry.category("actions").add("ecosphere.action_manager_dashboard", EsgManagerDashboard);
registry.category("actions").add("ecosphere.action_admin_dashboard", EsgAdminDashboard);
