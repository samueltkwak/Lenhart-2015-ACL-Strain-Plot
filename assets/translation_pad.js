(function () {
    function numberFromData(element, name) {
        return Number(element.dataset[name]);
    }

    function snap(value, step, minValue, maxValue) {
        var snapped = Math.round((value - minValue) / step) * step + minValue;
        return Math.min(maxValue, Math.max(minValue, snapped));
    }

    function setInputValue(input, value) {
        var setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,
            "value"
        ).set;
        setter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function setDotPosition(pad, dot, lateral, anterior) {
        var xMin = numberFromData(pad, "xMin");
        var xMax = numberFromData(pad, "xMax");
        var yMin = numberFromData(pad, "yMin");
        var yMax = numberFromData(pad, "yMax");
        var xPercent = ((lateral - xMin) / (xMax - xMin)) * 100;
        var yPercent = 100 - ((anterior - yMin) / (yMax - yMin)) * 100;

        dot.style.left = xPercent + "%";
        dot.style.top = yPercent + "%";
    }

    function readInputValue(input) {
        var parts = (input.value || "0,0").split(",");
        return {
            anterior: Number(parts[0]) || 0,
            lateral: Number(parts[1]) || 0,
        };
    }

    function publishTranslation(input, anterior, lateral) {
        setInputValue(input, anterior + "," + lateral);
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props("translation-store", {
                data: {
                    anterior: anterior,
                    lateral: lateral,
                },
            });
        }
    }

    function updateFromPointer(event, pad, dot, input) {
        var rect = pad.getBoundingClientRect();
        var xMin = numberFromData(pad, "xMin");
        var xMax = numberFromData(pad, "xMax");
        var xStep = numberFromData(pad, "xStep");
        var yMin = numberFromData(pad, "yMin");
        var yMax = numberFromData(pad, "yMax");
        var yStep = numberFromData(pad, "yStep");
        var xRatio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
        var yRatio = Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height));
        var lateral = snap(xMin + xRatio * (xMax - xMin), xStep, xMin, xMax);
        var anterior = snap(yMax - yRatio * (yMax - yMin), yStep, yMin, yMax);

        setDotPosition(pad, dot, lateral, anterior);
        publishTranslation(input, anterior, lateral);
    }

    function setupTranslationPad() {
        var pad = document.getElementById("translation-pad-control");
        var dot = document.getElementById("translation-dot");
        var input = document.getElementById("translation-input");

        if (!pad || !dot || !input || pad.dataset.initialized === "true") {
            return;
        }

        pad.dataset.initialized = "true";
        var initial = readInputValue(input);
        setDotPosition(pad, dot, initial.lateral, initial.anterior);

        var dragging = false;
        pad.addEventListener("pointerdown", function (event) {
            dragging = true;
            dot.classList.add("dragging");
            pad.setPointerCapture(event.pointerId);
            updateFromPointer(event, pad, dot, input);
        });

        pad.addEventListener("pointermove", function (event) {
            if (!dragging) {
                return;
            }
            updateFromPointer(event, pad, dot, input);
        });

        function stopDragging() {
            dragging = false;
            dot.classList.remove("dragging");
        }

        pad.addEventListener("pointerup", stopDragging);
        pad.addEventListener("pointercancel", stopDragging);
    }

    document.addEventListener("DOMContentLoaded", setupTranslationPad);
    new MutationObserver(setupTranslationPad).observe(document.body, {
        childList: true,
        subtree: true,
    });
})();
