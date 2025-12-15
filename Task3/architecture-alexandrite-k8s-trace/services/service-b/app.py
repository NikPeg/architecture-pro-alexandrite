#!/usr/bin/env python3
"""
Service B - отвечает на запросы от Service A
"""
from flask import Flask, jsonify
import os
import time
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Настройка OpenTelemetry
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "service-b"})
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

# Инструментация Flask
FlaskInstrumentor().instrument_app(app)

# Получение tracer
tracer = trace.get_tracer(__name__)


@app.route("/", methods=["GET"])
def handle_request():
    """
    Главный endpoint service-b
    """
    with tracer.start_as_current_span("service-b-handler") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", "/")
        
        # Имитация некоторой работы
        span.add_event("Processing request")
        time.sleep(0.1)  # Небольшая задержка для демонстрации
        
        # Имитация дополнительной работы
        with tracer.start_as_current_span("service-b-processing") as processing_span:
            processing_span.set_attribute("operation", "data_processing")
            time.sleep(0.05)
            processing_span.add_event("Data processed successfully")
        
        result = {
            "service": "service-b",
            "status": "success",
            "message": "Hello from service-b!"
        }
        
        span.set_attribute("http.status_code", 200)
        span.set_attribute("response.status", "success")
        span.add_event("Request processed successfully")
        
        return jsonify(result), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "service-b"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)

