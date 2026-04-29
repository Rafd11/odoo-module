/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

const DEBUG = typeof window !== "undefined" && (window.location.search.includes("square_debug=1") || sessionStorage.getItem("pos_square_debug") === "1");
// Enable debug from console: sessionStorage.setItem('pos_square_debug','1'); then refresh receipt screen

/** One-time document listener so Refund works even when something blocks the button's own listener */
function installRefundCapture() {
    if (window.__pos_square_refund_capture) return;
    window.__pos_square_refund_capture = true;
    document.addEventListener(
        "click",
        (ev) => {
            const btn = ev.target.closest && ev.target.closest("[data-square-refund]");
            if (!btn) return;
            const screen = window.__pos_square_receipt_screen;
            if (!screen || typeof screen.refundSquareInPos !== "function") return;
            ev.preventDefault();
            ev.stopPropagation();
            screen.refundSquareInPos().catch((err) => {
                console.error("[pos_square_terminal] Refund error", err);
                if (screen.notification) screen.notification.add(_t("Refund error: ") + (err && err.message || String(err)), { type: "danger", sticky: true });
            });
        },
        true
    );
}

function doRpc(env, route, params) {
    const rpcFn = env?.services?.rpc || rpc;
    if (typeof rpcFn === "function") {
        return Promise.resolve(rpcFn(route, params)).catch((err) => ({ error: err?.message || String(err) }));
    }
    if (typeof rpcFn?.request === "function") {
        return Promise.resolve(rpcFn.request(route, params)).catch((err) => ({ error: err?.message || String(err) }));
    }
    return Promise.resolve({ error: "RPC service not available" });
}

/** Show buttons whenever we have a current order (on Mac, payment lines may be empty after sync; we validate on click). */
function shouldShowSquareButtons(receiptScreen) {
    return !!receiptScreen.currentOrder;
}

/** Get the receipt screen root: smallest node with receipt content (current tab only, works on Mac + iPad). */
function getReceiptScreenRoot() {
    const doc = document;
    const candidates = [];
    doc.querySelectorAll("div").forEach((div) => {
        const t = (div.textContent || "").trim();
        if ((t.includes("Paiement réussi") || t.includes("Payment successful")) && (t.includes("Nouvelle commande") || t.includes("New order"))) {
            const n = div.querySelectorAll("*").length;
            if (n < 400) candidates.push({ div, n });
        }
    });
    if (candidates.length) {
        candidates.sort((a, b) => a.n - b.n);
        return candidates[0].div;
    }
    return doc.querySelector(".o_pos_ui") || doc.body;
}

/** Show debug message in console; if DEBUG or injection failed, show on-screen so user can see why on Mac. */
function showSquareDebug(msg, detail) {
    const full = "[pos_square_terminal] " + msg + (detail ? " " + JSON.stringify(detail) : "");
    console.log(full);
    const showOnScreen = DEBUG || (detail && detail.reason && detail.reason !== "ok" && detail.reason !== "already_injected");
    if (!showOnScreen) return;
    let el = document.getElementById("pos_square_terminal_debug");
    if (!el) {
        el = document.createElement("div");
        el.id = "pos_square_terminal_debug";
        el.style.cssText = "position:fixed;bottom:0;left:0;right:0;background:#333;color:#0f0;padding:8px 12px;font-family:monospace;font-size:12px;z-index:99999;max-height:120px;overflow:auto;";
        document.body.appendChild(el);
    }
    const line = full + (detail && detail.reason ? " (reason: " + detail.reason + ")" : "");
    el.innerHTML = line + "<br>" + (el.innerHTML || "").split("<br>").slice(0, 8).join("<br>");
}

/** Inject Square buttons into the receipt screen DOM; insert right after "Print full receipt" button. */
function injectSquareButtons(receiptScreen) {
    installRefundCapture();
    const step = { shouldShow: false, scope: null, buttonsInScope: 0, insertTarget: null, parent: null, injected: false, reason: "" };
    if (receiptScreen._squareButtonsInjected) {
        step.reason = "already_injected";
        showSquareDebug("inject skip", step);
        return;
    }
    step.shouldShow = shouldShowSquareButtons(receiptScreen);
    if (!step.shouldShow) {
        step.reason = "no_payment_lines";
        showSquareDebug("inject skip (no payment lines)", step);
        return;
    }
    document.querySelectorAll(".pos_square_terminal_buttons").forEach((el) => el.remove());
    const scope = getReceiptScreenRoot();
    step.scope = scope ? "found" : "null";
    if (!scope || !(scope instanceof HTMLElement)) {
        step.reason = "no_scope";
        showSquareDebug("inject fail: receipt panel not found", step);
        return;
    }
    const allButtons = scope.querySelectorAll("button");
    step.buttonsInScope = allButtons.length;
    let insertTarget = null;
    for (const btn of allButtons) {
        const text = (btn.textContent || btn.innerText || "").trim().toLowerCase();
        const hasImprimer = text.includes("imprimer") && (text.includes("reçu") || text.includes("receipt"));
        const hasPrint = text.includes("print") && text.includes("receipt");
        const hasNouvelle = text.includes("nouvelle") && text.includes("commande");
        const hasNewOrder = text.includes("new") && text.includes("order");
        if (hasImprimer || hasPrint) {
            insertTarget = { btn, after: true };
            break;
        }
        if ((hasNouvelle || hasNewOrder) && !insertTarget) {
            insertTarget = { btn, after: false };
        }
    }
    step.insertTarget = insertTarget ? (insertTarget.after ? "print_after" : "neworder_before") : "none";
    let parent;
    let insertBeforeNext = false;
    if (insertTarget) {
        parent = insertTarget.btn.parentElement;
        insertBeforeNext = insertTarget.after;
    } else {
        parent = scope.querySelector(".d-flex.flex-column") || scope.querySelector("[class*='col']") || scope.firstElementChild || scope;
    }
    step.parent = parent ? "found" : "null";
    if (!parent || !(parent instanceof HTMLElement)) {
        step.reason = "no_parent";
        showSquareDebug("inject fail: no parent to append to", step);
        return;
    }
    const wrap = document.createElement("div");
    wrap.className = "d-flex flex-column gap-2 mt-3 mb-2 pos_square_terminal_buttons";
    const btnPrint = document.createElement("button");
    btnPrint.type = "button";
    btnPrint.className = "btn btn-secondary";
    btnPrint.title = _t("Print receipt on the Square Terminal device");
    btnPrint.innerHTML = '<i class="fa fa-print"></i> ' + _t("Print on Square Terminal");
    btnPrint.addEventListener("click", () => receiptScreen.printReceiptOnSquareTerminal());
    const btnRefund = document.createElement("button");
    btnRefund.type = "button";
    btnRefund.className = "btn btn-warning";
    btnRefund.setAttribute("data-square-refund", "1");
    btnRefund.title = _t("Refund this payment on Square (stays in POS)");
    btnRefund.innerHTML = '<i class="fa fa-undo"></i> ' + _t("Refund on Square");
    btnRefund.style.cursor = "pointer";
    btnRefund.style.pointerEvents = "auto";
    const doRefund = async () => {
        try {
            if (receiptScreen.notification) receiptScreen.notification.add(_t("Opening refund form…"), { type: "info" });
            await receiptScreen.openRefundSquare();
        } catch (err) {
            console.error("[pos_square_terminal] Refund button error", err);
            const msg = (err && err.message) ? err.message : String(err);
            if (receiptScreen.notification) receiptScreen.notification.add(_t("Refund error: ") + msg, { type: "danger", sticky: true });
        }
    };
    btnRefund.addEventListener("click", (ev) => { ev.preventDefault(); ev.stopPropagation(); doRefund(); }, true);
    btnRefund.addEventListener("pointerdown", (ev) => { ev.preventDefault(); ev.stopPropagation(); doRefund(); }, true);
    wrap.appendChild(btnPrint);
    wrap.appendChild(btnRefund);
    const targetBtn = insertTarget && insertTarget.btn;
    if (insertBeforeNext && targetBtn) {
        targetBtn.insertAdjacentElement("afterend", wrap);
    } else if (targetBtn) {
        targetBtn.insertAdjacentElement("beforebegin", wrap);
    } else {
        parent.appendChild(wrap);
    }
    receiptScreen._squareButtonsInjected = true;
    window.__pos_square_receipt_screen = receiptScreen;
    step.injected = true;
    step.reason = "ok";
    showSquareDebug("inject OK", step);
}

const _originalReceiptScreenSetup = ReceiptScreen.prototype.setup;
patch(ReceiptScreen.prototype, {
    setup() {
        _originalReceiptScreenSetup.call(this, ...arguments);
        this._squarePaymentsFromBackend = [];
        onMounted(async () => {
            const self = this;
            showSquareDebug("ReceiptScreen mounted", { orderId: self.currentOrder?.id, hasOrder: !!self.currentOrder });
            const orderId = self.currentOrder && typeof self.currentOrder.id === "number" ? self.currentOrder.id : null;
            if (orderId) {
                const res = await doRpc(self.env, "/pos_square_terminal/order_square_payments", { order_id: orderId });
                if (res && res.payments && res.payments.length) {
                    self._squarePaymentsFromBackend = res.payments;
                }
            }
            const tick = () => injectSquareButtons(self);
            // Retry over 4s so injection works on both iPad and Mac (desktop often renders later)
            setTimeout(tick, 50);
            setTimeout(tick, 200);
            setTimeout(tick, 500);
            setTimeout(tick, 900);
            setTimeout(tick, 1400);
            setTimeout(tick, 2000);
            setTimeout(tick, 2800);
            setTimeout(tick, 4000);
            // MutationObserver: inject as soon as receipt content appears (fixes Mac when DOM updates late)
            const observer = new MutationObserver(() => {
                if (self._squareButtonsInjected) {
                    observer.disconnect();
                    return;
                }
                tick();
            });
            const observeTarget = document.body;
            observer.observe(observeTarget, { childList: true, subtree: true });
            setTimeout(() => observer.disconnect(), 6000);
        });
    },

    /** Add company website to receipt data so OrderReceipt can show QR code. */
    generateTicketImage(isBasicReceipt = false) {
        const order = this.currentOrder;
        const data = this.pos.orderExportForPrinting(order);
        if (data) {
            if (this.pos.company?.website) data.company_website = this.pos.company.website;
            data.receipt_served_by = this.pos.employee?.name || "";
            data.receipt_order_ref = order.name || order.pos_reference || order.uid || "";
        }
        return this.renderer.toJpeg(
            OrderReceipt,
            {
                data,
                formatCurrency: this.env.utils.formatCurrency,
                basic_receipt: isBasicReceipt,
            },
            { addClass: "pos-receipt-print p-3" }
        );
    },

    /** Square Terminal payments: from backend (synced order) or from frontend payment lines. */
    get squarePayments() {
        const fromBackend = this._squarePaymentsFromBackend;
        if (fromBackend && fromBackend.length) return fromBackend;
        const order = this.currentOrder;
        if (!order) return [];
        const lines = order.get_paymentlines ? order.get_paymentlines() : (order.paymentlines || []);
        if (!Array.isArray(lines)) return [];
        return lines
            .filter((l) => l && (l.squarePaymentId || l.square_payment_id))
            .map((l) => ({
                payment_id: l.squarePaymentId || l.square_payment_id,
                amount: l.amount,
                payment_method_id: typeof l.payment_method_id === "object" ? l.payment_method_id?.id : l.payment_method_id,
            }));
    },

    /** Send receipt to Square Terminal for each Square payment of this order. */
    async printReceiptOnSquareTerminal() {
        let list = this.squarePayments;
        if (!list.length && this.currentOrder && typeof this.currentOrder.id === "number") {
            const res = await doRpc(this.env, "/pos_square_terminal/order_square_payments", { order_id: this.currentOrder.id });
            if (res && res.payments && res.payments.length) {
                this._squarePaymentsFromBackend = res.payments;
                list = res.payments;
            }
        }
        if (!list.length) {
            this.notification.add(_t("No Square Terminal payment for this order."), { type: "warning" });
            return;
        }
        for (const p of list) {
            const res = await doRpc(this.env, "/pos_square_terminal/issue_receipt", {
                payment_id: p.payment_id,
                payment_method_id: p.payment_method_id,
                print_only: true,
            });
            if (res && res.error) {
                this.notification.add(res.error, { type: "danger" });
                return;
            }
        }
        this.notification.add(_t("Receipt sent to Square Terminal."), { type: "success" });
    },

    /**
     * Refund this order's Square payment in-POS: confirm dialog then API call. No new page or redirect.
     */
    async refundSquareInPos() {
        const order = this.currentOrder;
        const orderId = typeof order.id === "number" ? order.id : null;
        if (!orderId) {
            this.notification.add(
                _t("Order not yet synced. Wait a moment or refund from Point of Sale → Square Terminal payments."),
                { type: "warning" }
            );
            return;
        }
        let list = this.squarePayments;
        if (!list.length) {
            const res = await doRpc(this.env, "/pos_square_terminal/order_square_payments", { order_id: orderId });
            if (res && res.payments && res.payments.length) {
                this._squarePaymentsFromBackend = res.payments;
                list = res.payments;
            }
        }
        if (!list.length) {
            this.notification.add(_t("No Square Terminal payment for this order."), { type: "warning" });
            return;
        }
        const first = list[0];
        const amount = first.amount != null ? first.amount : (order.get_total_paid ? order.get_total_paid() : 0);
        const currency = order.currency_id || this.pos?.currency || {};
        const symbol = currency.symbol || (currency.name === "USD" ? "$" : "€");
        const formatted = this.env.utils && this.env.utils.formatCurrency
            ? this.env.utils.formatCurrency(amount, currency)
            : `${symbol} ${Number(amount).toFixed(2)}`;
        const msg = _t("Refund %s on Square? (full amount to card)").replace("%s", formatted);
        if (!window.confirm(msg)) return;
        this.notification.add(_t("Refunding…"), { type: "info" });
        const res = await doRpc(this.env, "/pos_square_terminal/refund_order_square", {
            order_id: orderId,
            reason: "Odoo POS refund",
        });
        if (res && res.error) {
            this.notification.add(res.error, { type: "danger", sticky: true });
            return;
        }
        this.notification.add(_t("Refund sent to Square. Money will return to the card in a few days."), { type: "success" });
    },
});
