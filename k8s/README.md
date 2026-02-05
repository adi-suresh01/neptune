# Neptune Kubernetes Notes

## Ingress + TLS

- Ingress expects `neptune.local` and `ollama.local`.
- Create a self-signed cert:
  ```bash
  ./scripts/k8s_tls.sh
  ```
- Update your `/etc/hosts` (server or local) to point to the ingress IP:
  ```
  <INGRESS_IP> neptune.local
  <INGRESS_IP> ollama.local
  ```

## DNS (Optional)

If you have a DNS provider, create A records for:
- `neptune.yourdomain.com` → ingress IP
- `ollama.yourdomain.com` → ingress IP

Then update `k8s/ingress.yaml` hosts accordingly.
