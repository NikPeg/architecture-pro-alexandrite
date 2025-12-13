#!/bin/bash
set -e

echo "🚀 Запуск развёртывания Jaeger и сервисов..."

# Проверка наличия необходимых инструментов
echo "📋 Проверка инструментов..."
command -v minikube >/dev/null 2>&1 || { echo "❌ Minikube не установлен. Установите: brew install minikube"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl не установлен. Установите: brew install kubectl"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker не установлен"; exit 1; }

echo "✅ Все инструменты установлены"

# 1. Запуск Minikube
echo ""
echo "1️⃣ Запуск Minikube..."
if ! minikube status >/dev/null 2>&1; then
    minikube start --addons=ingress
else
    echo "   Minikube уже запущен"
fi

# 2. Установка cert-manager
echo ""
echo "2️⃣ Установка cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml || echo "   cert-manager уже установлен"

# 3. Развертывание Jaeger
echo ""
echo "3️⃣ Развертывание Jaeger..."
kubectl create namespace observability 2>/dev/null || echo "   Namespace observability уже существует"

echo "   Установка Jaeger Operator..."
kubectl create -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml -n observability 2>/dev/null || echo "   Jaeger Operator уже установлен"

echo "   Ожидание готовности Jaeger Operator..."
kubectl wait --for=condition=ready pod -l name=jaeger-operator -n observability --timeout=120s 2>/dev/null || echo "   Jaeger Operator готов или уже работает"

echo "   Развертывание Jaeger instance..."
kubectl apply -f k8s/jaeger-instance.yaml

echo "   Ожидание готовности Jaeger..."
sleep 10
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=jaeger -n observability --timeout=120s 2>/dev/null || echo "   Ожидание готовности Jaeger..."

# 4. Сборка и деплой сервисов
echo ""
echo "4️⃣ Сборка образов сервисов..."
echo "   Сборка service-a..."
minikube image build -t service-a:latest services/service-a/

echo "   Сборка service-b..."
minikube image build -t service-b:latest services/service-b/

echo ""
echo "5️⃣ Развертывание сервисов..."
kubectl apply -f k8s/services.yaml

echo "   Ожидание готовности сервисов..."
sleep 10
kubectl wait --for=condition=ready pod -l app=service-a --timeout=120s 2>/dev/null || echo "   Сервисы запускаются..."

echo ""
echo "✅ Развёртывание завершено!"
echo ""
echo "📊 Следующие шаги:"
echo "   1. Откройте Jaeger UI:"
echo "      kubectl port-forward svc/simplest-query 16686:16686"
echo "      Затем откройте в браузере: http://localhost:16686"
echo ""
echo "   2. Выполните тестовый запрос:"
echo "      kubectl exec -it \$(kubectl get pods -l app=service-a -o jsonpath='{.items[0].metadata.name}') -- curl http://service-a:8080"
echo ""
echo "   3. В Jaeger UI выберите сервис 'service-a' и нажмите 'Find Traces'"
echo "   4. Сделайте скриншот трейса"

