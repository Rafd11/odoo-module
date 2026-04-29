/** ********************************************************************************
 *
 *    Copyright (C) 2020 Cetmix OÜ
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU LESSER GENERAL PUBLIC LICENSE for more details.
 *
 *    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 **********************************************************************************/

/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {_t} from "@web/core/l10n/translation";
import {rpc} from "@web/core/network/rpc";
import {registry} from "@web/core/registry";
import {WARNING_MESSAGE, WKHTMLTOPDF_MESSAGES, _getReportUrl} from "./tools.esm";

let wkhtmltopdfStateProm = null;

registry.category("ir.actions.report handlers").add(
    "open_report_handler",
    async function (action, options, env) {
        if (action.type === "ir.actions.report" && action.report_type === "qweb-pdf") {
            // Check the state of wkhtmltopdf before proceeding
            if (!wkhtmltopdfStateProm) {
                wkhtmltopdfStateProm = rpc("/report/check_wkhtmltopdf");
            }
            const state = await wkhtmltopdfStateProm;
            if (state in WKHTMLTOPDF_MESSAGES) {
                env.services.notification.add(WKHTMLTOPDF_MESSAGES[state], {
                    sticky: true,
                    title: _t("Report"),
                });
            }
            if (state === "upgrade" || state === "ok") {
                // Trigger the download of the PDF report
                const url = _getReportUrl(action, "pdf", env);
                // AAB: this check should be done in get_file service directly,
                // should not be the concern of the caller (and that way, get_file
                // could return a deferred)
                try {
                    const newWindow = browser.open(url, "_blank");
                    if (!newWindow) {
                        env.services.notification.add(WARNING_MESSAGE, {
                            type: "warning",
                        });
                    }
                } catch {
                    env.services.notification.add(WARNING_MESSAGE, {
                        type: "warning",
                    });
                }
            } else {
                // Fallback: open the HTML version when wkhtmltopdf is not available
                try {
                    const htmlUrl = _getReportUrl(action, "html", env);
                    const newWindow = browser.open(htmlUrl, "_blank");
                    if (!newWindow) {
                        env.services.notification.add(WARNING_MESSAGE, {
                            type: "warning",
                        });
                    }
                } catch {
                    env.services.notification.add(WARNING_MESSAGE, {type: "warning"});
                }
            }
            return true;
        }
        return false;
    },
    {sequence: 10}
);
