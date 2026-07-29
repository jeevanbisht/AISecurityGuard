import base64
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "build" / "aci-deployment.yaml"


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {name}")
    return value


def get_base64_file(path):
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def main():
    registry_server = require_env("ACR_SERVER")
    registry_username = require_env("ACR_USERNAME")
    registry_password = require_env("ACR_PASSWORD")
    location = os.getenv("AZURE_LOCATION", "westus3")
    resource_name = os.getenv("ACI_RESOURCE_NAME", "envoy-ai-guard")
    dns_label = os.getenv("ACI_DNS_LABEL", "envoy-ai-guard-demo")
    guard_image = os.getenv(
        "AI_GUARD_IMAGE",
        f"{registry_server}/ai-model-service:latest",
    )
    web_image = os.getenv(
        "WEB_IMAGE",
        f"{registry_server}/webserver:latest",
    )

    envoy_yaml_b64 = get_base64_file(ROOT / "envoy-azure.yaml")
    envoy_crt_b64 = get_base64_file(ROOT / "certs" / "envoy.crt")
    envoy_key_b64 = get_base64_file(ROOT / "certs" / "envoy.key")

    aci_yaml_content = f"""apiVersion: '2021-10-01'
location: {location}
name: {resource_name}
properties:
  containers:
  - name: envoy
    properties:
      image: envoyproxy/envoy:v1.30-latest
      resources:
        requests:
          cpu: 1.0
          memoryInGB: 1.0
      ports:
      - port: 8080
        protocol: TCP
      - port: 8443
        protocol: TCP
      volumeMounts:
      - name: envoy-config-vol
        mountPath: /etc/envoy
  - name: ai-model-service
    properties:
      image: {guard_image}
      resources:
        requests:
          cpu: 0.5
          memoryInGB: 1.5
  - name: webserver
    properties:
      image: {web_image}
      resources:
        requests:
          cpu: 0.5
          memoryInGB: 0.5
  imageRegistryCredentials:
  - server: {registry_server}
    username: {registry_username}
    password: {registry_password}
  osType: Linux
  ipAddress:
    type: Public
    dnsNameLabel: {dns_label}
    ports:
    - port: 8080
      protocol: TCP
    - port: 8443
      protocol: TCP
  volumes:
  - name: envoy-config-vol
    secret:
      envoy.yaml: {envoy_yaml_b64}
      envoy.crt: {envoy_crt_b64}
      envoy.key: {envoy_key_b64}
type: Microsoft.ContainerInstance/containerGroups
"""

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(aci_yaml_content, encoding="utf-8")
    print(f"Generated deployment manifest: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
