#!/usr/bin/env python3
"""
Service A - вызывает Service B
"""
from flask import Flask, jsonify
import requests
import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Настройка OpenTelemetry
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "service-a"})
    )
)

# Настройка Jaeger Exporter
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "simplest-agent"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
)

# Добавление span processor
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Создание приложения Flask
app = Flask(__name__)

# Инструментация Flask и requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Получение tracer
tracer = trace.get_tracer(__name__)

# URL service-b
SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8080")


@app.route("/", methods=["GET"])
def call_service_b():
    """
    Главный endpoint, который вызывает service-b
    """
    with tracer.start_as_current_span("service-a-handler") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", "/")
        
        try:
            # Вызов service-b
            span.add_event("Calling service-b")
            response = requests.get(SERVICE_B_URL, timeout=5)
            response.raise_for_status()
            
            result = {
                "service": "service-a",
                "status": "success",
                "service_b_response": response.json()
            }
            
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("response.status", "success")
            span.add_event("Service-b call completed successfully")
            
            return jsonify(result), 200
            
        except requests.exceptions.RequestException as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            result = {
                "service": "service-a",
                "status": "error",
                "error": str(e)
            }
            
            return jsonify(result), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "service-a"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)

