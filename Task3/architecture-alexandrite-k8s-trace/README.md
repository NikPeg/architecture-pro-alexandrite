# Jaeger в Minikube с сервисами

## Описание
Развертывание Jaeger в Minikube с двумя сервисами, которые:
1. Взаимодействуют между собой
2. Отправляют трейсы в Jaeger

## Требования
- Minikube
- kubectl
- Docker

## Установка

### 1. Запуск Minikube 
```bash
minikube start --addons=ingress 
```
Ingress нужен для вызовов

### 2. Установка cert-manager
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
```

### 3. Развертывание Jaeger
```bash
kubectl create namespace observability
kubectl create -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml -n observability

# Подождите, пока Jaeger Operator будет готов (обычно 30-60 секунд)
kubectl wait --for=condition=ready pod -l name=jaeger-operator -n observability --timeout=120s

# Развертывание Jaeger instance
kubectl apply -f k8s/jaeger-instance.yaml

# Подождите, пока Jaeger будет готов
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=jaeger -n observability --timeout=120s
```

### 4. Сборка и деплой сервисов
```bash
# Сборка образов
minikube image build -t service-a:latest services/service-a/
minikube image build -t service-b:latest services/service-b/

# Развертывание
kubectl apply -f k8s/services.yaml

# Подождите, пока сервисы будут готовы
kubectl wait --for=condition=ready pod -l app=service-a --timeout=120s
kubectl wait --for=condition=ready pod -l app=service-b --timeout=120s
```

## Проверка работы

### Доступ к Jaeger UI
```bash
kubectl port-forward svc/simplest-query 16686:16686
```
Откройте в браузере: http://localhost:16686

### Тестирование сервисов
```bash
# Вызов service-a, который вызывает service-b
# Убедитесь, что в поде установлен wget или curl
kubectl exec -it $(kubectl get pods -l app=service-a -o jsonpath='{.items[0].metadata.name}') -- wget -qO- http://service-a:8080

# Или используйте curl (если wget недоступен)
kubectl exec -it $(kubectl get pods -l app=service-a -o jsonpath='{.items[0].metadata.name}') -- curl http://service-a:8080

# Проверка логов service-a
kubectl logs -l app=service-a --tail=50

# Проверка логов service-b
kubectl logs -l app=service-b --tail=50
```

## Поиск трейса в Jaeger UI

После выполнения тестового запроса:

1. Откройте Jaeger UI: http://localhost:16686
2. В левой панели выберите сервис "service-a" из выпадающего списка
3. Нажмите кнопку "Find Traces"
4. Вы должны увидеть трейс, который показывает:
   - Вызов service-a-handler
   - Внутри него вызов service-b-handler
   - Время выполнения каждого span
5. Кликните на трейс, чтобы увидеть детали
6. **Сделайте скриншот** и сохраните его в папку Task3

## Структура проекта
- `services/service-a/` - Исходный код service-a
- `services/service-b/` - Исходный код service-b  
- `k8s/services.yaml` - Конфигурация Kubernetes для сервисов
- `k8s/jaeger-instance.yaml` - Конфигурация Jaeger