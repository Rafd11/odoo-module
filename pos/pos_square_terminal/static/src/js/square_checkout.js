/** @odoo-module **/

(function () {
    "use strict";

    function initSquareCheckout() {
        var wrapper = document.getElementById("square_checkout_wrapper");
        if (!wrapper) return;

        var applicationId = wrapper.getAttribute("data-application-id");
        var locationId = wrapper.getAttribute("data-location-id") || undefined;
        var form = document.getElementById("square-payment-form");
        var sourceInput = document.getElementById("square_source_id");
        var submitBtn = document.getElementById("square-submit-btn");
        var errorDiv = document.getElementById("square-error");

        function showError(msg) {
            if (errorDiv) {
                errorDiv.textContent = msg || "An error occurred.";
                errorDiv.classList.remove("d-none");
            }
        }

        function hideError() {
            if (errorDiv) errorDiv.classList.add("d-none");
        }

        if (!applicationId || !form) return;

        if (typeof Square === "undefined") {
            setTimeout(initSquareCheckout, 100);
            return;
        }

        var payments;
        try {
            payments = Square.payments(applicationId, locationId);
        } catch (e) {
            showError("Failed to initialize Square: " + (e.message || e));
            return;
        }

        var card;
        payments.card().then(function (cardInstance) {
            card = cardInstance;
            return card.attach("#square-card-container");
        }).then(function () {
            if (submitBtn) submitBtn.disabled = false;
        }).catch(function (e) {
            showError("Failed to load card form: " + (e.message || e));
        });

        form.addEventListener("submit", function (e) {
            e.preventDefault();
            if (!card) return;
            hideError();
            if (submitBtn) submitBtn.disabled = true;
            card.tokenize().then(function (result) {
                if (result.status === "OK" && result.token) {
                    sourceInput.value = result.token;
                    form.submit();
                } else {
                    showError(result.errors && result.errors[0] ? result.errors[0].message : "Tokenization failed.");
                    if (submitBtn) submitBtn.disabled = false;
                }
            }).catch(function (err) {
                showError(err.message || "Tokenization failed.");
                if (submitBtn) submitBtn.disabled = false;
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSquareCheckout);
    } else {
        initSquareCheckout();
    }
})();
