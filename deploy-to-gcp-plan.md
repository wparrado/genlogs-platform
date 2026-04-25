# Plan de despliegue en GCP

Objetivo
- Desplegar el frontend como SPA en Firebase Hosting y el backend (FastAPI) en GCP de la forma más simple y segura posible, con métricas y trazabilidad enviadas a Google Cloud (Managed Service for Prometheus / Cloud Monitoring y Cloud Trace) usando Prometheus y OpenTelemetry.

Arquitectura propuesta (alta nivel)
- Frontend: SPA (Vite/React/Vue) desplegada en Firebase Hosting.
- Backend: FastAPI empaquetado en contenedor y desplegado en Cloud Run (servicio serverless). Base de datos: Cloud SQL (Postgres) si se requiere persistencia.
- Observabilidad:
  - Métricas: exponer /api/metrics con prometheus_client; en Cloud Run enviar métricas a Cloud Monitoring usando OpenTelemetry Metrics -> Cloud Monitoring exporter o usar el cliente de Cloud Monitoring. (Managed Prometheus es ideal en GKE; para Cloud Run se recomienda exportar a Cloud Monitoring directamente.)
  - Trazas: instrumentar con OpenTelemetry SDK y exportar a Cloud Trace vía OTLP/Cloud Trace exporter (preferible) o enviar a un Collector si se usa GKE.

Pre-requisitos GCP
- Cuenta de GCP y proyecto creado.
- Habilitar APIs: Cloud Run, Cloud Build, Artifact Registry, Cloud SQL Admin (si aplica), Monitoring API, Cloud Trace API, Logging API.
- Crear Service Account para despliegues con roles mínimos: Cloud Run Admin (para despliegue), Artifact Registry Writer, Monitoring Metric Writer, Cloud Trace Agent (o roles equivalentes) y Logging Writer. Preferir asignar service account a Cloud Run en vez de poner claves en la app.

Pasos detallados

1) Preparar el frontend (Firebase Hosting)
- Configurar el build de la SPA (npm run build) y probar artefacto localmente.
- Instalar Firebase CLI y autenticar: firebase login
- Inicializar hosting: firebase init hosting (seleccionar build output directory)
- Configurar rewrites para que la SPA sirva index.html en rutas desconocidas.
- Desplegar: firebase deploy --only hosting

2) Empaquetar backend (Cloud Run)
- Confirmar Dockerfile (ya existe). Ajustar si hace falta (incluir instalación de dependencias OTEL en pyproject.toml y sincronizar imagen).
- Construir imagen y subir a Artifact Registry (o Container Registry):
  - gcloud artifacts repositories create ... (si no existe)
  - gcloud builds submit --tag LOCATION-docker.pkg.dev/PROJECT/REPO/genlogs-backend:tag
- Crear o reutilizar Service Account para Cloud Run y asignar permisos.
- Desplegar a Cloud Run:
  - gcloud run deploy genlogs-backend --image=... --platform managed --region=... --service-account=... --allow-unauthenticated (según necesidad)
- Configurar variables de entorno en el servicio (PROJECT_ID, OTEL_EXPORTER_OTLP_ENDPOINT si aplica, INSTANCE_CONNECTION_NAME para Cloud SQL, etc.)

3) Base de datos (opcional)
- Si la app usa Postgres: crear instancia Cloud SQL Postgres.
- Conectar Cloud Run a Cloud SQL usando Cloud SQL Auth Connector (agregar --add-cloudsql-instances y configurar IAM Service Account con role cloudsql.client).

4) Instrumentación: métricas y trazas
- Dependencias: añadir a pyproject.toml (ejemplo):
  - opentelemetry-api, opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-requests, opentelemetry-exporter-otlp
  - (Opcional) google-cloud-monitoring or opentelemetry-exporter-google-cloud si se prefiere exportador nativo
- Trazas:
  - Usar app.telemetry.init_tracing() para configurar OTLP endpoint o exportador directo a Cloud Trace.
  - Para Cloud Run: preferir usar el exporter que habla directamente con Cloud Trace (si existe) o usar OTLP exporter apuntando al collector gestionado; también se puede usar Cloud Trace client libraries.
- Métricas:
  - Mantener /api/metrics expuesto por prometheus_client para tests y scraping local.
  - En Cloud Run, enviar métricas a Cloud Monitoring mediante OpenTelemetry Metrics exporter -> Cloud Monitoring o escribir métricas con google-cloud-monitoring client.
  - Alternativa avanzada: si se usa GKE, exponer /metrics y usar Managed Service for Prometheus (ServiceMonitor)

5) Opciones con OpenTelemetry Collector
- Si se despliega en GKE: desplegar Collector (DaemonSet) y configurar receiver OTLP y exporters a Cloud Monitoring / Cloud Trace y remote_write a Managed Prometheus.
- Si se mantiene Cloud Run: no es trivial correr Collector como sidecar; mejor usar exporters directos o desplegar Collector en un pequeño GKE cluster para centralizar.

6) Autenticación y secretos
- No almacenar JSON keys en el repositorio.
- Para Cloud Run: asignar Service Account al servicio o usar Secret Manager + variables de entorno para secretos.
- Para Firebase Hosting usar la cuenta de Firebase CLI para deploy; no subir claves al repo.

7) CI/CD
- Frontend: automatizar build y deploy con GitHub Actions o Cloud Build + Firebase CLI.
- Backend: usar Cloud Build/GitHub Actions para construir y publicar imagen a Artifact Registry, luego gcloud run deploy.

8) Validación y pruebas
- Verificar que la SPA está servida correctamente por Firebase.
- Llamar al backend y comprobar logs en Cloud Logging.
- Verificar trazas en Cloud Trace (buscar spans con request path).
- Verificar métricas en Cloud Monitoring (custom metrics) o Managed Prometheus según la ruta elegida.

9) Observabilidad y alertas
- Crear dashboards con métricas clave: latencia, errores 5xx, tasa de requests, rate limiting.
- Crear alertas para errores altos y latencias.

Tareas (checklist)
- [ ] Habilitar APIs en GCP
- [ ] Crear Service Accounts y asignar roles
- [ ] Añadir dependencias OTEL al backend
- [ ] Ajustar Dockerfile e imágenes
- [ ] Desplegar backend en Cloud Run
- [ ] Desplegar frontend en Firebase Hosting
- [ ] Configurar envío de trazas a Cloud Trace
- [ ] Configurar envío de métricas a Cloud Monitoring (o Managed Prometheus si se usa GKE)
- [ ] Validación E2E y crear dashboards

Notas y recomendaciones
- Para simplicidad y menor gestión operar el backend en Cloud Run y usar Cloud Monitoring/Cloud Trace exporters directos en la app.
- Si se busca compatibilidad completa con Managed Prometheus y Prometheus scraping, preferir desplegar en GKE y usar ServiceMonitor + OTEL Collector.
- Priorizar seguridad: usar service accounts y Secret Manager; no volcar credenciales en imágenes o repo.

Referencias rápidas
- Managed Service for Prometheus: https://cloud.google.com/stackdriver/docs/managed-prometheus
- OTLP/OTEL metrics to Cloud Monitoring: https://cloud.google.com/stackdriver/docs/otlp-metrics/overview
- Firebase Hosting: https://firebase.google.com/docs/hosting
- Cloud Run deploying: https://cloud.google.com/run/docs/deploying
