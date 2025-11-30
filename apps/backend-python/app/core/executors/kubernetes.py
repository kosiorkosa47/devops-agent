"""
Kubernetes Operations Executor
"""
import logging
from typing import Dict, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class KubernetesExecutor:
    """Execute Kubernetes operations"""
    
    def __init__(self):
        try:
            # Try in-cluster config first, then kubeconfig
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
            
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            
            logger.info("Kubernetes client initialized successfully")
        except Exception as e:
            logger.warning(f"Kubernetes config not found: {e}")
            self.v1 = None
    
    async def kubectl_get_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> Dict[str, Any]:
        """List pods"""
        try:
            if not self.v1:
                return {"error": "Kubernetes not configured"}
            
            if namespace:
                pods = self.v1.list_namespaced_pod(namespace, label_selector=label_selector)
            else:
                pods = self.v1.list_pod_for_all_namespaces(label_selector=label_selector)
            
            result = []
            for pod in pods.items:
                result.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "ready": sum(1 for c in (pod.status.container_statuses or []) if c.ready),
                    "total_containers": len(pod.spec.containers),
                    "restarts": sum(c.restart_count for c in (pod.status.container_statuses or [])),
                    "age": str(pod.metadata.creation_timestamp)
                })
            
            return {
                "success": True,
                "pods": result,
                "count": len(result)
            }
        
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error listing pods: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def kubectl_get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        container: Optional[str] = None,
        tail_lines: int = 100,
        follow: bool = False
    ) -> Dict[str, Any]:
        """Get pod logs"""
        try:
            if not self.v1:
                return {"error": "Kubernetes not configured"}
            
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                follow=follow
            )
            
            return {
                "success": True,
                "pod": pod_name,
                "namespace": namespace,
                "container": container,
                "logs": logs
            }
        
        except ApiException as e:
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error getting logs: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def kubectl_describe_pod(self, namespace: str, pod_name: str) -> Dict[str, Any]:
        """Describe pod (detailed info)"""
        try:
            if not self.v1:
                return {"error": "Kubernetes not configured"}
            
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            events = self.v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pod_name}"
            )
            
            return {
                "success": True,
                "pod": {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "labels": pod.metadata.labels,
                    "annotations": pod.metadata.annotations,
                    "status": pod.status.phase,
                    "conditions": [
                        {"type": c.type, "status": c.status, "reason": c.reason}
                        for c in (pod.status.conditions or [])
                    ],
                    "containers": [
                        {
                            "name": c.name,
                            "image": c.image,
                            "ready": c.ready if pod.status.container_statuses else False,
                            "restarts": c.restart_count if pod.status.container_statuses else 0
                        }
                        for c in pod.spec.containers
                    ],
                    "node": pod.spec.node_name,
                    "created": str(pod.metadata.creation_timestamp)
                },
                "events": [
                    {
                        "type": e.type,
                        "reason": e.reason,
                        "message": e.message,
                        "time": str(e.last_timestamp)
                    }
                    for e in events.items[-10:]  # Last 10 events
                ]
            }
        
        except ApiException as e:
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error describing pod: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def kubectl_get_deployments(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """List deployments"""
        try:
            if not self.apps_v1:
                return {"error": "Kubernetes not configured"}
            
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace)
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces()
            
            result = []
            for dep in deployments.items:
                result.append({
                    "name": dep.metadata.name,
                    "namespace": dep.metadata.namespace,
                    "replicas": dep.spec.replicas,
                    "ready_replicas": dep.status.ready_replicas or 0,
                    "available_replicas": dep.status.available_replicas or 0,
                    "image": dep.spec.template.spec.containers[0].image if dep.spec.template.spec.containers else "N/A"
                })
            
            return {
                "success": True,
                "deployments": result,
                "count": len(result)
            }
        
        except ApiException as e:
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error listing deployments: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def kubectl_scale_deployment(self, namespace: str, deployment_name: str, replicas: int) -> Dict[str, Any]:
        """⚠️ DANGEROUS: Scale deployment"""
        try:
            if not self.apps_v1:
                return {"error": "Kubernetes not configured"}
            
            # Validate replicas count
            if replicas < 0 or replicas > 50:
                return {"error": "Replicas must be between 0 and 50"}
            
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(deployment_name, namespace)
            
            # Update replicas
            deployment.spec.replicas = replicas
            self.apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=namespace,
                body={"spec": {"replicas": replicas}}
            )
            
            return {
                "success": True,
                "deployment": deployment_name,
                "namespace": namespace,
                "previous_replicas": deployment.spec.replicas,
                "new_replicas": replicas,
                "message": f"Scaled {deployment_name} to {replicas} replicas"
            }
        
        except ApiException as e:
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error scaling deployment: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def kubectl_delete_pod(self, namespace: str, pod_name: str) -> Dict[str, Any]:
        """⚠️ DANGEROUS: Delete pod"""
        try:
            if not self.v1:
                return {"error": "Kubernetes not configured"}
            
            self.v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
            
            return {
                "success": True,
                "pod": pod_name,
                "namespace": namespace,
                "message": f"Pod {pod_name} deleted (will be recreated if managed by deployment)"
            }
        
        except ApiException as e:
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error deleting pod: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def kubectl_get_events(self, namespace: Optional[str] = None, resource_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Kubernetes events"""
        try:
            if not self.v1:
                return {"error": "Kubernetes not configured"}
            
            field_selector = f"involvedObject.name={resource_name}" if resource_name else None
            
            if namespace:
                events = self.v1.list_namespaced_event(namespace, field_selector=field_selector)
            else:
                events = self.v1.list_event_for_all_namespaces(field_selector=field_selector)
            
            result = []
            for event in sorted(events.items, key=lambda e: e.last_timestamp or e.first_timestamp, reverse=True)[:50]:
                result.append({
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "object": event.involved_object.name,
                    "namespace": event.involved_object.namespace,
                    "time": str(event.last_timestamp or event.first_timestamp)
                })
            
            return {
                "success": True,
                "events": result,
                "count": len(result)
            }
        
        except ApiException as e:
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error getting events: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def kubectl_top_pods(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get pod resource usage (requires metrics-server)"""
        try:
            # This requires metrics-server to be installed
            # For now, return a placeholder
            return {
                "success": True,
                "message": "Pod metrics require metrics-server to be installed in the cluster",
                "note": "Use kubectl top pods command directly or deploy metrics-server"
            }
        except Exception as e:
            logger.error(f"Error getting pod metrics: {e}", exc_info=True)
            return {"error": str(e)}
