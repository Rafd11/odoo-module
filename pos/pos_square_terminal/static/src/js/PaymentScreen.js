/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

const SQUARE_POLL_INTERVAL_MS = 1500;
const SQUARE_POLL_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

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

/** Build a rich note for Square checkout: order number, served by, items, website (shows on terminal/receipt). */
function buildOrderNoteForSquare(self) {
    const order = self.currentOrder;
    const pos = self.pos;
    if (!order) return "";
    const parts = [];
    // Order number (like Odoo receipt: "Commande 00022-012-0007")
    const orderName = order.name || order.uid || (order.pos_reference && String(order.pos_reference)) || "";
    if (orderName) parts.push(orderName);
    // Served by (cashier)
    const cashier = pos?.employee?.name ?? order.employee_id?.name ?? order.cashier?.name ?? pos?.user?.name ?? "";
    if (cashier) parts.push("Servi par " + cashier);
    // Line items
    const lines = order.get_orderlines ? order.get_orderlines() : (order.orderlines || order.getOrderlines?.() || []);
    if (Array.isArray(lines) && lines.length) {
        const names = [];
        for (const l of lines) {
            const name = l.get_product?.()?.display_name ?? l.product_id?.display_name ?? l.product_name ?? l.product?.display_name ?? "";
            const qty = l.quantity ?? l.get_quantity?.() ?? 1;
            if (name) names.push(qty > 1 ? `${qty}× ${name}` : name);
        }
        if (names.length) parts.push(names.join(", "));
    }
    // Website (no QR on Square receipt; show URL so they can type it)
    const website = pos?.company?.website ?? pos?.config?.company_id?.website ?? "";
    if (website) {
        const clean = website.replace(/^https?:\/\//i, "").split("/")[0];
        if (clean) parts.push("Site: " + clean);
    }
    return parts.join(" | ").slice(0, 500) || "";
}

function runSquareTerminalPayment(self, line) {
    const paymentMethod = line.payment_method_id;
    if (!paymentMethod || !isSquarePaymentMethod(paymentMethod)) return null;
    const amount = line.amount;
    const currency = self.pos?.currency?.name || "USD";
    const note = buildOrderNoteForSquare(self) || undefined;
    return doRpc(self.env, "/pos_square_terminal/create_checkout", {
        amount: amount,
        currency: currency,
        payment_method_id: paymentMethod.id,
        reference: self.currentOrder?.name || undefined,
        note: note,
    });
}

function setSquareStatus(self, msg) {
    self._squareStatusMessage = msg;
    try {
        if (self.__owl__ && self.render) self.render();
    } catch (_) {}
}

async function pollSquareCheckoutStatusWithCancel(self, checkoutId, paymentMethodId, line, cancelRef) {
    const start = Date.now();
    let lastStatusResult = null;
    while (Date.now() - start < SQUARE_POLL_TIMEOUT_MS) {
        if (cancelRef.cancelRequested) return null;
        await new Promise((r) => setTimeout(r, SQUARE_POLL_INTERVAL_MS));
        if (cancelRef.cancelRequested) return null;
        lastStatusResult = await doRpc(self.env, "/pos_square_terminal/checkout_status", {
            checkout_id: checkoutId,
            payment_method_id: paymentMethodId,
        });
        if (lastStatusResult && lastStatusResult.error) {
            setSquareStatus(self, "");
            self.env.services.notification.add(lastStatusResult.error, { type: "danger" });
            return false;
        }
        const status = (lastStatusResult && lastStatusResult.status) || "";
        if (status === "COMPLETED") return lastStatusResult;
        if (status === "CANCELED" || status === "CANCELED_BY_SELLER" || status === "EXPIRED") {
            setSquareStatus(self, _t("Refused / Canceled"));
            self.env.services.notification.add(
                _t("Payment canceled or expired on terminal."),
                { type: "warning" }
            );
            return false;
        }
        setSquareStatus(self, _t("In progress… (pay on terminal)"));
    }
    setSquareStatus(self, _t("Timed out"));
    self.env.services.notification.add(_t("Square Terminal payment timed out."), {
        type: "danger",
    });
    return false;
}

/** Run Square flow with amount + method; returns { success, payment_ids } or { success: false }. No line yet. */
async function runSquareFlowForAmount(self, amount, paymentMethod) {
    if (!amount || amount <= 0 || !isSquarePaymentMethod(paymentMethod)) return { success: false };
    const fakeLine = { amount, payment_method_id: paymentMethod };
    self.pos.paymentTerminalInProgress = true;
    self._squareStatusMessage = _t("Connecting to Square…");
    const cancelRef = { cancelRequested: false };
    self._squareCancelRef = cancelRef;
    self._squareCurrentCheckoutId = null;
    self._squareCurrentPaymentMethodId = null;
    if (self.numberBuffer && self.numberBuffer.capture) self.numberBuffer.capture();
    const createResult = await runSquareTerminalPayment(self, fakeLine);
    if (createResult && createResult.error) {
        setSquareStatus(self, _t("Error"));
        self.env.services.notification.add(createResult.error, { type: "danger" });
        self.pos.paymentTerminalInProgress = false;
        self._squareCancelRef = null;
        self._squareStatusMessage = "";
        return { success: false };
    }
    if (!createResult?.checkout_id) {
        setSquareStatus(self, _t("Error"));
        self.env.services.notification.add(_t("Square: no checkout ID"), { type: "danger" });
        self.pos.paymentTerminalInProgress = false;
        self._squareCancelRef = null;
        self._squareStatusMessage = "";
        return { success: false };
    }
    self._squareCurrentCheckoutId = createResult.checkout_id;
    self._squareCurrentPaymentMethodId = paymentMethod.id;
    setSquareStatus(self, _t("Waiting for payment on terminal…"));
    self.env.services.notification.add(
        _t("Waiting for payment on Square Terminal… (pay on device or Cancel)"),
        { type: "info" }
    );
    const result = await pollSquareCheckoutStatusWithCancel(
        self,
        createResult.checkout_id,
        paymentMethod.id,
        fakeLine,
        cancelRef
    );
    self._squareCurrentCheckoutId = null;
    self._squareCurrentPaymentMethodId = null;
    self._squareCancelRef = null;
    self.pos.paymentTerminalInProgress = false;
    self._squareStatusMessage = "";
    try {
        if (self.__owl__ && self.render) self.render();
    } catch (_) {}
    if (result && result.payment_ids && result.payment_ids.length) {
        setSquareStatus(self, _t("Completed"));
        return { success: true, payment_ids: result.payment_ids };
    }
    return { success: false };
}

function getAmountForNewPayment(self) {
    const order = self.currentOrder;
    if (!order) return 0;
    let amount = 0;
    if (typeof order.get_due === "function") amount = order.get_due();
    if (!amount && order.get_due != null) amount = order.get_due;
    if (!amount && order.amount_due != null) amount = order.amount_due;
    if (!amount && order.amount_total != null) amount = order.amount_total;
    if (!amount && typeof order.get_total_with_tax === "function") amount = order.get_total_with_tax();
    if (!amount && self.numberBuffer) {
        if (typeof self.numberBuffer.get === "function") amount = self.numberBuffer.get();
        else if (self.numberBuffer.value != null) amount = self.numberBuffer.value;
    }
    return Number(amount) || 0;
}

/** Resolve payment method record from a line (Odoo 18 may have payment_method_id as id or record). */
function getPaymentMethodFromLine(pos, line) {
    if (!line) return null;
    const pm = line.payment_method_id;
    if (!pm) return null;
    if (typeof pm === "object" && (pm.use_square_terminal !== undefined || pm.name !== undefined || pm.id !== undefined)) return pm;
    const id = typeof pm === "number" ? pm : (pm && pm.id);
    if (id == null) return null;
    const config = pos?.config;
    if (config?.payment_method_ids) {
        const found = config.payment_method_ids.find((m) => m.id === id);
        if (found) return found;
    }
    try {
        const models = pos?.models;
        if (models?.["pos.payment.method"]) {
            const rec = models["pos.payment.method"].get(id);
            if (rec) return rec;
        }
    } catch (_) {}
    return pm;
}

function isSquarePaymentMethod(paymentMethod) {
    if (!paymentMethod) return false;
    if (paymentMethod.use_square_terminal === true || paymentMethod.use_square_terminal === "true") return true;
    const name = (paymentMethod.name || paymentMethod.display_name || "").toString().toLowerCase();
    if (name.includes("square")) return true;
    return false;
}

/** Get numeric payment method id from line (for RPC). */
function getPaymentMethodIdForRpc(pos, line) {
    const method = getPaymentMethodFromLine(pos, line) || line?.payment_method_id;
    if (method == null) return null;
    if (typeof method === "number") return method;
    return method.id != null ? method.id : null;
}

function lineIsSquareWithoutPaymentId(pos, line) {
    if (!line || !(line.amount > 0)) return false;
    if (line.squarePaymentId) return false;
    const method = getPaymentMethodFromLine(pos, line);
    if (isSquarePaymentMethod(method)) return true;
    const id = getPaymentMethodIdForRpc(pos, line);
    if (id == null) return false;
    const config = pos?.config;
    if (config?.payment_method_ids) {
        const squareMethod = config.payment_method_ids.find(
            (m) => m.id === id && (m.use_square_terminal || (m.name || "").toLowerCase().includes("square"))
        );
        if (squareMethod) return true;
    }
    return false;
}

async function runSquareFlowForLine(self, line) {
    let paymentMethod = getPaymentMethodFromLine(self.pos, line) || (line && line.payment_method_id);
    if (!paymentMethod || !isSquarePaymentMethod(paymentMethod)) return;
    const methodId = getPaymentMethodIdForRpc(self.pos, line);
    if (methodId == null) return;
    if (typeof paymentMethod !== "object" || paymentMethod.id == null) {
        paymentMethod = { id: methodId, name: "Square" };
    }
    const lineForRpc = { ...line, payment_method_id: paymentMethod };
    self.pos.paymentTerminalInProgress = true;
    self._squareStatusMessage = _t("Connecting to Square…");
    const cancelRef = { cancelRequested: false };
    self._squareCancelRef = cancelRef;
    self._squareCurrentCheckoutId = null;
    self._squareCurrentPaymentMethodId = null;
    if (self.numberBuffer && self.numberBuffer.capture) self.numberBuffer.capture();
    const paymentLines = self.paymentLines || [];
    paymentLines.forEach((l) => {
        if (l.can_be_reversed !== undefined) l.can_be_reversed = false;
    });
    const createResult = await runSquareTerminalPayment(self, lineForRpc);
    if (createResult && createResult.error) {
        setSquareStatus(self, _t("Error"));
        self.env.services.notification.add(createResult.error, { type: "danger" });
        self.pos.paymentTerminalInProgress = false;
        self._squareCancelRef = null;
        self._squareStatusMessage = "";
        return;
    }
    if (!createResult || !createResult.checkout_id) {
        setSquareStatus(self, _t("Error"));
        self.env.services.notification.add(
            _t("Square: no checkout ID"),
            { type: "danger" }
        );
        self.pos.paymentTerminalInProgress = false;
        self._squareCancelRef = null;
        self._squareStatusMessage = "";
        return;
    }
    self._squareCurrentCheckoutId = createResult.checkout_id;
    self._squareCurrentPaymentMethodId = paymentMethod.id;
    setSquareStatus(self, _t("Waiting for payment on terminal…"));
    self.env.services.notification.add(
        _t("Waiting for payment on Square Terminal… (Cancel from terminal or wait)"),
        { type: "info" }
    );
    const result = await pollSquareCheckoutStatusWithCancel(
        self,
        createResult.checkout_id,
        paymentMethod.id,
        line,
        cancelRef
    );
    self._squareCurrentCheckoutId = null;
    self._squareCurrentPaymentMethodId = null;
    self._squareCancelRef = null;
    if (result) {
        setSquareStatus(self, _t("Completed"));
        if (line.set_payment_status) line.set_payment_status("done");
        if (result.payment_ids && result.payment_ids.length && line.squarePaymentId === undefined) {
            try {
                const squareId = result.payment_ids[0];
                line.squarePaymentId = squareId;
                line.square_payment_id = squareId; // for server payload when order is saved
            } catch (_) {}
        }
        const config = self.pos?.config;
        const currentOrder = line.pos_order_id || self.currentOrder;
        if (
            currentOrder &&
            config?.auto_validate_terminal_payment &&
            currentOrder.is_paid &&
            currentOrder.is_paid()
        ) {
            if (self.validateOrder) self.validateOrder(false);
        }
    }
    self.pos.paymentTerminalInProgress = false;
    self._squareStatusMessage = "";
    try {
        if (self.__owl__ && self.render) self.render();
    } catch (_) {}
}

async function cancelSquareCheckout(self) {
    const checkoutId = self._squareCurrentCheckoutId;
    const paymentMethodId = self._squareCurrentPaymentMethodId;
    if (!checkoutId || !paymentMethodId || !self._squareCancelRef) return;
    try {
        await doRpc(self.env, "/pos_square_terminal/cancel_checkout", {
            checkout_id: checkoutId,
            payment_method_id: paymentMethodId,
        });
    } catch (_) {}
    self._squareCancelRef.cancelRequested = true;
    self.env.services.notification.add(_t("Cancel requested. Waiting for terminal…"), { type: "info" });
}

try {
    const _superAddNewPaymentLine = PaymentScreen.prototype.addNewPaymentLine;
    const _superSendPaymentRequest = PaymentScreen.prototype.sendPaymentRequest;
    const _superValidateOrder = PaymentScreen.prototype.validateOrder;
    const _superFinalizeValidation = PaymentScreen.prototype._finalizeValidation;

    patch(PaymentScreen.prototype, {
        async addNewPaymentLine(paymentMethod) {
            try {
                if (!isSquarePaymentMethod(paymentMethod)) {
                    return _superAddNewPaymentLine.apply(this, arguments);
                }
                const amount = getAmountForNewPayment(this);
                if (amount === 0 || amount === null || amount === undefined || (typeof amount === "number" && isNaN(amount))) {
                    this.env.services.notification.add(_t("Enter amount first, then select Square Terminal."), { type: "warning" });
                    return false;
                }
                // Refund (negative amount): record in Odoo and send refund to Square here (no redirect).
                if (amount < 0) {
                    const result = await _superAddNewPaymentLine.apply(this, arguments);
                    if (!result) return result;
                    const order = this.currentOrder;
                    const originalOrderId =
                        order?.refunded_order_id != null
                            ? (typeof order.refunded_order_id === "object" ? order.refunded_order_id.id : order.refunded_order_id)
                            : null;
                    if (originalOrderId && typeof originalOrderId === "number") {
                        this.env.services.notification.add(_t("Refunding on Square…"), { type: "info" });
                        const refundRes = await doRpc(this.env, "/pos_square_terminal/refund_order_square", {
                            order_id: originalOrderId,
                            amount: Math.abs(amount),
                            reason: "Odoo POS refund",
                        });
                        if (refundRes && refundRes.error) {
                            this.env.services.notification.add(
                                _t("Refund recorded in Odoo. Square: ") + refundRes.error,
                                { type: "warning", sticky: true }
                            );
                        } else {
                            this.env.services.notification.add(
                                _t("Refund recorded and sent to Square. Money will return to the card."),
                                { type: "success" }
                            );
                        }
                    } else {
                        this.env.services.notification.add(
                            _t("Refund recorded. To refund on Square, use Point of Sale → Square Terminal payments."),
                            { type: "info" }
                        );
                    }
                    return result;
                }
                this.env.services.notification.add(_t("Sending to Square Terminal…"), { type: "info" });
                const squareResult = await runSquareFlowForAmount(this, amount, paymentMethod);
                if (!squareResult.success) {
                    return false;
                }
                if (!squareResult.payment_ids || !squareResult.payment_ids.length) {
                    return false;
                }
                try {
                    if (this.numberBuffer) {
                        if (typeof this.numberBuffer.set === "function") this.numberBuffer.set(amount);
                        else if (typeof this.numberBuffer.setValue === "function") this.numberBuffer.setValue(amount);
                    }
                } catch (_) {}
                const result = await _superAddNewPaymentLine.apply(this, arguments);
                if (result && squareResult.payment_ids && squareResult.payment_ids.length) {
                    const paymentLines = this.paymentLines || [];
                    const newLine = paymentLines.at(paymentLines.length - 1);
                    if (newLine) {
                        try {
                            newLine.squarePaymentId = squareResult.payment_ids[0];
                            newLine.square_payment_id = squareResult.payment_ids[0];
                            if (typeof newLine.set_payment_status === "function") newLine.set_payment_status("done");
                        } catch (_) {}
                    }
                    try {
                        const order = this.currentOrder;
                        if (order && this.pos?.config?.auto_validate_terminal_payment && typeof order.is_paid === "function" && order.is_paid()) {
                            if (typeof this.validateOrder === "function") this.validateOrder(false);
                        }
                    } catch (_) {}
                }
                return result;
            } catch (err) {
                console.error("[pos_square_terminal] addNewPaymentLine error:", err);
                if (this.env?.services?.notification) {
                    this.env.services.notification.add(_t("Square Terminal error."), { type: "warning" });
                }
                return await _superAddNewPaymentLine.apply(this, arguments);
            }
        },
        async sendPaymentRequest(line) {
            try {
                const method = getPaymentMethodFromLine(this.pos, line);
                if (isSquarePaymentMethod(method)) {
                    if (line.squarePaymentId) {
                        return;
                    }
                    await runSquareFlowForLine(this, line);
                    return;
                }
            } catch (err) {
                console.error("[pos_square_terminal] sendPaymentRequest error:", err);
                if (this.env?.services?.notification) {
                    this.env.services.notification.add(_t("Square Terminal error."), { type: "danger" });
                }
            }
            return _superSendPaymentRequest.apply(this, arguments);
        },
        async cancelSquareCheckout() {
            try {
                return await cancelSquareCheckout(this);
            } catch (_) {}
        },
        get isSquareCheckoutInProgress() {
            try {
                return Boolean(this._squareCurrentCheckoutId);
            } catch (_) {
                return false;
            }
        },
        get squareStatusMessage() {
            try {
                return this._squareStatusMessage || "";
            } catch (_) {
                return "";
            }
        },
        async validateOrder(isOrderComplete) {
            // Run Square flow first for any Square line not yet sent to terminal (before _isOrderValid / _finalizeValidation).
            try {
                const lines = this.paymentLines || [];
                const squareMethodIds = new Set();
                const config = this.pos?.config;
                if (config?.payment_method_ids) {
                    config.payment_method_ids.forEach((m) => {
                        if (m.use_square_terminal || (m.name || "").toLowerCase().includes("square")) {
                            squareMethodIds.add(m.id);
                        }
                    });
                }
                const squareLinesWithoutId = lines.filter((l) => {
                    if (!l || !(l.amount > 0) || l.squarePaymentId) return false;
                    if (lineIsSquareWithoutPaymentId(this.pos, l)) return true;
                    const linePmId = getPaymentMethodIdForRpc(this.pos, l);
                    return linePmId != null && squareMethodIds.has(linePmId);
                });
                if (squareLinesWithoutId.length > 0) {
                    for (const line of squareLinesWithoutId) {
                        this.env.services.notification.add(_t("Sending to Square Terminal…"), { type: "info" });
                        await runSquareFlowForLine(this, line);
                        if (!line.squarePaymentId) {
                            this.env.services.notification.add(
                                _t("Square Terminal payment did not complete. Complete on terminal or cancel."),
                                { type: "danger" }
                            );
                            return;
                        }
                    }
                }
            } catch (err) {
                console.error("[pos_square_terminal] validateOrder error:", err);
                if (this.env?.services?.notification) {
                    this.env.services.notification.add(_t("Square Terminal error."), { type: "warning" });
                }
            }
            return _superValidateOrder.apply(this, arguments);
        },
        async _finalizeValidation() {
            // Safety net: ensure no Square line is finalized without squarePaymentId.
            try {
                const lines = this.paymentLines || [];
                const squareMethodIds = new Set();
                const config = this.pos?.config;
                if (config?.payment_method_ids) {
                    config.payment_method_ids.forEach((m) => {
                        if (m.use_square_terminal || (m.name || "").toLowerCase().includes("square")) {
                            squareMethodIds.add(m.id);
                        }
                    });
                }
                const squareLinesWithoutId = lines.filter((l) => {
                    if (!l || !(l.amount > 0) || l.squarePaymentId) return false;
                    if (lineIsSquareWithoutPaymentId(this.pos, l)) return true;
                    const linePmId = getPaymentMethodIdForRpc(this.pos, l);
                    return linePmId != null && squareMethodIds.has(linePmId);
                });
                if (squareLinesWithoutId.length > 0) {
                    for (const line of squareLinesWithoutId) {
                        this.env.services?.notification?.add(_t("Sending to Square Terminal…"), { type: "info" });
                        await runSquareFlowForLine(this, line);
                        if (!line.squarePaymentId) {
                            this.env.services?.notification?.add(
                                _t("Square Terminal payment not completed. Cannot finalize."),
                                { type: "danger" }
                            );
                            return;
                        }
                    }
                }
            } catch (err) {
                console.error("[pos_square_terminal] _finalizeValidation error:", err);
                if (this.env?.services?.notification) {
                    this.env.services.notification.add(_t("Square Terminal error."), { type: "danger" });
                }
                return;
            }
            return _superFinalizeValidation.apply(this, arguments);
        },
    });
} catch (e) {
    console.warn("[pos_square_terminal] Patch failed, Square Terminal will not be available:", e);
}
