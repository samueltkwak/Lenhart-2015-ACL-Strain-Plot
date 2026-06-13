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

    function setDotPosition(pad, dot, xValue, yValue) {
        var xMin = numberFromData(pad, "xMin");
        var xMax = numberFromData(pad, "xMax");
        var yMin = numberFromData(pad, "yMin");
        var yMax = numberFromData(pad, "yMax");
        var xPercent = ((xValue - xMin) / (xMax - xMin)) * 100;
        var yPercent = 100 - ((yValue - yMin) / (yMax - yMin)) * 100;

        dot.style.left = xPercent + "%";
        dot.style.top = yPercent + "%";
    }

    function readInputValue(pad, input) {
        var parts = (input.value || "0,0").split(",");
        var first = Number(parts[0]) || 0;
        var second = Number(parts[1]) || 0;

        if (pad.dataset.inputOrder === "y,x") {
            return { x: second, y: first };
        }
        return { x: first, y: second };
    }

    function inputValueForPad(pad, xValue, yValue) {
        if (pad.dataset.inputOrder === "y,x") {
            return yValue + "," + xValue;
        }
        return xValue + "," + yValue;
    }

    function syncDotFromInput(pad, dot, input) {
        var current = readInputValue(pad, input);
        setDotPosition(pad, dot, current.x, current.y);
    }

    function publishPadValue(pad, input, xValue, yValue) {
        var xKey = pad.dataset.xKey;
        var yKey = pad.dataset.yKey;
        var storeId = pad.dataset.storeId;
        var data = {};

        data[xKey] = xValue;
        data[yKey] = yValue;
        setInputValue(input, inputValueForPad(pad, xValue, yValue));

        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props(storeId, { data: data });
        }
    }

    function valueFromPointer(event, pad) {
        var rect = pad.getBoundingClientRect();
        var xMin = numberFromData(pad, "xMin");
        var xMax = numberFromData(pad, "xMax");
        var xStep = numberFromData(pad, "xStep");
        var yMin = numberFromData(pad, "yMin");
        var yMax = numberFromData(pad, "yMax");
        var yStep = numberFromData(pad, "yStep");
        var xRatio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
        var yRatio = Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height));
        var xValue = snap(xMin + xRatio * (xMax - xMin), xStep, xMin, xMax);
        var yValue = snap(yMax - yRatio * (yMax - yMin), yStep, yMin, yMax);

        return { x: xValue, y: yValue };
    }

    function updateDotFromPointer(event, pad, dot) {
        var value = valueFromPointer(event, pad);
        setDotPosition(pad, dot, value.x, value.y);
        return value;
    }

    function setupPad(pad) {
        var dot = document.getElementById(pad.dataset.dotId);
        var input = document.getElementById(pad.dataset.inputId);
        var resetButton = document.getElementById("reset-kinematics");

        if (!dot || !input || pad.dataset.initialized === "true") {
            return;
        }

        pad.dataset.initialized = "true";
        syncDotFromInput(pad, dot, input);
        input.addEventListener("input", function () {
            syncDotFromInput(pad, dot, input);
        });
        input.addEventListener("change", function () {
            syncDotFromInput(pad, dot, input);
        });
        if (resetButton) {
            resetButton.addEventListener("click", function () {
                publishPadValue(pad, input, 0, 0);
                setDotPosition(pad, dot, 0, 0);
            });
        }

        var dragging = false;
        var pendingValue = null;
        pad.addEventListener("pointerdown", function (event) {
            if (event.pointerType === "touch") {
                event.preventDefault();
            }
            dragging = true;
            dot.classList.add("dragging");
            pad.setPointerCapture(event.pointerId);
            pendingValue = updateDotFromPointer(event, pad, dot);
        });

        pad.addEventListener("pointermove", function (event) {
            if (!dragging) {
                return;
            }
            if (event.pointerType === "touch") {
                event.preventDefault();
            }
            pendingValue = updateDotFromPointer(event, pad, dot);
        });

        function stopDragging() {
            if (pendingValue) {
                publishPadValue(pad, input, pendingValue.x, pendingValue.y);
            }
            pendingValue = null;
            dragging = false;
            dot.classList.remove("dragging");
        }

        pad.addEventListener("pointerup", stopDragging);
        pad.addEventListener("pointercancel", stopDragging);
    }

    function setupKinematicPads() {
        var pads = document.querySelectorAll(".kinematic-pad-control");
        pads.forEach(setupPad);
    }

    document.addEventListener("DOMContentLoaded", setupKinematicPads);
    new MutationObserver(setupKinematicPads).observe(document.body, {
        childList: true,
        subtree: true,
    });
})();
