(function () {
    if (window.__aclInteractionsLoaded) {
        return;
    }
    window.__aclInteractionsLoaded = true;

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

    function pointerDistance(first, second) {
        var dx = first.x - second.x;
        var dy = first.y - second.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function cloneCamera(camera) {
        return {
            eye: Object.assign({}, camera.eye || {}),
            center: Object.assign({}, camera.center || {}),
            up: Object.assign({}, camera.up || {}),
        };
    }

    function cameraFromGraph(graph) {
        var scene = graph && graph._fullLayout && graph._fullLayout.scene;

        if (scene && scene._scene && typeof scene._scene.getCamera === "function") {
            return cloneCamera(scene._scene.getCamera());
        }
        if (graph && graph._lastCamera) {
            return cloneCamera(graph._lastCamera);
        }
        if (scene && scene.camera) {
            return cloneCamera(scene.camera);
        }
        if (graph && graph.layout && graph.layout.scene && graph.layout.scene.camera) {
            return cloneCamera(graph.layout.scene.camera);
        }
        return {};
    }

    function cameraFromRelayout(eventData, graph) {
        var camera = cameraFromGraph(graph);

        if (!eventData) {
            return null;
        }
        if (eventData["scene.camera"]) {
            return cloneCamera(eventData["scene.camera"]);
        }
        if (eventData["scene.camera.eye"]) {
            camera.eye = Object.assign({}, eventData["scene.camera.eye"]);
        }
        if (eventData["scene.camera.center"]) {
            camera.center = Object.assign({}, eventData["scene.camera.center"]);
        }
        if (eventData["scene.camera.up"]) {
            camera.up = Object.assign({}, eventData["scene.camera.up"]);
        }

        if (
            eventData["scene.camera.eye"] ||
            eventData["scene.camera.center"] ||
            eventData["scene.camera.up"]
        ) {
            return camera;
        }
        return null;
    }

    function scaledCamera(camera, scale) {
        var nextCamera = cloneCamera(camera);
        var eye = nextCamera.eye || {};

        nextCamera.eye = {
            x: (Number(eye.x) || 0) * scale,
            y: (Number(eye.y) || 0) * scale,
            z: (Number(eye.z) || 0) * scale,
        };
        return nextCamera;
    }

    function clampScale(scale) {
        return Math.min(2.8, Math.max(0.35, scale));
    }

    function setupPlotPinchZoom(container) {
        if (!container) {
            return;
        }

        if (!container.querySelector(".js-plotly-plot") || !window.Plotly) {
            return;
        }

        function activePointerList() {
            return Object.keys(container._pinchZoomPointers || {}).map(function (pointerId) {
                return container._pinchZoomPointers[pointerId];
            });
        }

        function graphDiv() {
            return container.querySelector(".js-plotly-plot");
        }

        function storeCamera(camera) {
            var graph = graphDiv();
            if (graph && camera) {
                graph._lastCamera = cloneCamera(camera);
            }
        }

        function bindCameraListener() {
            var graph = graphDiv();
            if (!graph || typeof graph.on !== "function" || graph._pinchZoomRelayoutBound) {
                return;
            }

            graph._pinchZoomRelayoutBound = true;
            graph.on("plotly_relayout", function (eventData) {
                var camera = cameraFromRelayout(eventData, graphDiv());
                if (camera) {
                    storeCamera(camera);
                }
            });
        }

        bindCameraListener();

        if (container.dataset.pinchZoomInitialized === "true") {
            return;
        }

        container._pinchZoomPointers = {};
        container._pinchZoomStartDistance = null;
        container._pinchZoomStartCamera = null;
        container.dataset.pinchZoomInitialized = "true";

        function beginPinchIfReady(event) {
            var graph = graphDiv();
            var pointers = activePointerList();
            if (pointers.length !== 2 || !graph._fullLayout || !graph._fullLayout.scene) {
                return;
            }

            if (container.setPointerCapture && event.pointerId !== undefined) {
                try {
                    container.setPointerCapture(event.pointerId);
                } catch (error) {
                    // Pointer capture can fail if the browser has already released it.
                }
            }

            container._pinchZoomStartDistance = pointerDistance(pointers[0], pointers[1]);
            container._pinchZoomStartCamera = cameraFromGraph(graph);
            storeCamera(container._pinchZoomStartCamera);
        }

        function updatePinch(event) {
            if (!container._pinchZoomStartDistance || !container._pinchZoomStartCamera) {
                return;
            }

            var graph = graphDiv();
            var pointers = activePointerList();
            if (pointers.length !== 2 || !graph) {
                return;
            }

            var currentDistance = pointerDistance(pointers[0], pointers[1]);
            if (!currentDistance) {
                return;
            }

            event.preventDefault();
            var scale = clampScale(container._pinchZoomStartDistance / currentDistance);
            var nextCamera = scaledCamera(container._pinchZoomStartCamera, scale);
            storeCamera(nextCamera);
            window.Plotly.relayout(graph, {
                "scene.camera": nextCamera,
            });
        }

        function clearPointer(pointerId) {
            delete container._pinchZoomPointers[pointerId];
            if (activePointerList().length < 2) {
                container._pinchZoomStartDistance = null;
                container._pinchZoomStartCamera = null;
            }
        }

        container.addEventListener("pointerdown", function (event) {
            if (event.pointerType !== "touch") {
                return;
            }

            container._pinchZoomPointers[event.pointerId] = { x: event.clientX, y: event.clientY };
            if (activePointerList().length >= 2) {
                event.preventDefault();
                beginPinchIfReady(event);
            }
        });

        container.addEventListener("pointermove", function (event) {
            if (event.pointerType !== "touch" || !container._pinchZoomPointers[event.pointerId]) {
                return;
            }

            container._pinchZoomPointers[event.pointerId] = { x: event.clientX, y: event.clientY };
            updatePinch(event);
        });

        container.addEventListener("pointerup", function (event) {
            clearPointer(event.pointerId);
        });
        container.addEventListener("pointercancel", function (event) {
            clearPointer(event.pointerId);
        });
        container.addEventListener("pointerleave", function (event) {
            clearPointer(event.pointerId);
        });
    }

    function setupPlotPinchZooms() {
        ["surface-plot-pl", "surface-plot-am", "anatomy-plot"].forEach(function (plotId) {
            setupPlotPinchZoom(document.getElementById(plotId));
        });
    }

    document.addEventListener("DOMContentLoaded", setupKinematicPads);
    document.addEventListener("DOMContentLoaded", setupPlotPinchZooms);
    new MutationObserver(setupKinematicPads).observe(document.body, {
        childList: true,
        subtree: true,
    });
    new MutationObserver(setupPlotPinchZooms).observe(document.body, {
        childList: true,
        subtree: true,
    });
})();
