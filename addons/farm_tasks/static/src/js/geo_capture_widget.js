/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class GeoCaptureWidget extends Component {
    static template = "farm_tasks.GeoCaptureWidget";
    static props = ["*"];

    get latField() {
        return this.props.latField || "start_latitude";
    }

    get lngField() {
        return this.props.lngField || "start_longitude";
    }

    get latValue() {
        return this.props.record.data[this.latField];
    }

    get lngValue() {
        return this.props.record.data[this.lngField];
    }

    get hasCoords() {
        return !!this.latValue && !!this.lngValue;
    }

    captureLocation() {
        if (!("geolocation" in navigator)) {
            this.env.services.notification.add(
                "Геолокация не поддерживается этим браузером",
                { type: "warning" }
            );
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.props.record.update({
                    [this.latField]: position.coords.latitude,
                    [this.lngField]: position.coords.longitude,
                });
            },
            (error) => {
                this.env.services.notification.add(
                    "Не удалось определить местоположение: " + error.message,
                    { type: "danger" }
                );
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }
}

export const geoCaptureWidget = {
    component: GeoCaptureWidget,
    extractProps: ({ options }) => ({
        latField: options.lat_field,
        lngField: options.lng_field,
    }),
};

registry.category("fields").add("geo_capture", geoCaptureWidget);
