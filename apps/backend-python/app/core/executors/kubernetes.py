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
    
    async def analyze_resource_efficiency(self, namespace: str = "default") -> Dict[str, Any]:
        """
        Analyze resource efficiency for pods in namespace
        Compares actual usage vs limits
        """
        try:
            # Get pods
            pods_result = await self.kubectl_get_pods(namespace=namespace)
            if "error" in pods_result:
                return pods_result
            
            # Get metrics (top pods)
            metrics_result = await self.kubectl_top_pods(namespace=namespace)
            if "error" in metrics_result:
                return {"warning": "Metrics not available", "pods": pods_result["pods"]}
            
            recommendations = []
            
            for pod in pods_result.get("pods", []):
                pod_name = pod["name"]
                
                # Find corresponding metrics
                pod_metrics = next(
                    (m for m in metrics_result.get("pods", []) if m["name"] == pod_name),
                    None
                )
                
                if not pod_metrics:
                    continue
                
                # Parse resources
                containers = pod.get("containers", [])
                if not containers:
                    continue
                
                for container in containers:
                    limits = container.get("limits", {})
                    requests = container.get("requests", {})
                    
                    cpu_limit = limits.get("cpu", "0")
                    mem_limit = limits.get("memory", "0")
                    
                    # Simple CPU analysis (this is simplified)
                    if cpu_limit and cpu_limit != "0":
                        # Extract numeric value (very simplified)
                        try:
                            cpu_limit_val = float(cpu_limit.replace("m", "")) / 1000
                            cpu_usage_val = float(pod_metrics.get("cpu", "0m").replace("m", "")) / 1000
                            
                            if cpu_limit_val > 0:
                                cpu_usage_pct = (cpu_usage_val / cpu_limit_val) * 100
                                
                                if cpu_usage_pct < 20:
                                    recommendations.append({
                                        "pod": pod_name,
                                        "container": container.get("name"),
                                        "type": "over-provisioned-cpu",
                                        "current_limit": cpu_limit,
                                        "usage_percent": round(cpu_usage_pct, 2),
                                        "recommendation": f"Consider reducing CPU limit (only using {cpu_usage_pct:.1f}%)"
                                    })
                                elif cpu_usage_pct > 80:
                                    recommendations.append({
                                        "pod": pod_name,
                                        "container": container.get("name"),
                                        "type": "under-provisioned-cpu",
                                        "current_limit": cpu_limit,
                                        "usage_percent": round(cpu_usage_pct, 2),
                                        "recommendation": f"Consider increasing CPU limit ({cpu_usage_pct:.1f}% usage)"
                                    })
                        except:
                            pass
            
            return {
                "success": True,
                "namespace": namespace,
                "pods_analyzed": len(pods_result.get("pods", [])),
                "recommendations": recommendations,
                "summary": {
                    "over_provisioned": len([r for r in recommendations if "over" in r["type"]]),
                    "under_provisioned": len([r for r in recommendations if "under" in r["type"]])
                }
            }
        
        except Exception as e:
            logger.error(f"Error analyzing efficiency: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def auto_restart_pod(self, namespace: str, pod_name: str) -> Dict[str, Any]:
        """
        SELF-HEALING: Automatically restart a failed pod
        This is a destructive operation
        """
        try:
            if not self.core_v1:
                return {"error": "Kubernetes not configured"}
            
            # Delete the pod (it will be recreated by controller)
            logger.info(f"AUTO-HEALING: Restarting pod {pod_name} in {namespace}")
            
            self.core_v1.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace,
                grace_period_seconds=0
            )
            
            return {
                "success": True,
                "action": "pod_restarted",
                "pod": pod_name,
                "namespace": namespace,
                "message": f"Pod {pod_name} deleted and will be recreated automatically"
            }
        
        except ApiException as e:
            return {"error": f"Kubernetes API error: {e.reason}"}
        except Exception as e:
            logger.error(f"Error restarting pod: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def auto_scale_if_needed(self, namespace: str, deployment: str, max_replicas: int = 10) -> Dict[str, Any]:
        """
        SELF-HEALING: Automatically scale deployment if pods are struggling
        """
        try:
            # Get deployment info
            dep_result = await self.kubectl_get_deployments(namespace=namespace)
            if "error" in dep_result:
                return dep_result
            
            # Find our deployment
            target_dep = next(
                (d for d in dep_result.get("deployments", []) if d["name"] == deployment),
                None
            )
            
            if not target_dep:
                return {"error": f"Deployment {deployment} not found"}
            
            current_replicas = target_dep["replicas"]
            ready_replicas = target_dep["ready_replicas"]
            
            # Check if we need scaling
            if ready_replicas < current_replicas:
                # Pods are not ready, might need more replicas
                if current_replicas < max_replicas:
                    new_replicas = min(current_replicas + 1, max_replicas)
                    
                    logger.info(f"AUTO-HEALING: Scaling {deployment} from {current_replicas} to {new_replicas}")
                    
                    scale_result = await self.kubectl_scale_deployment(
                        namespace=namespace,
                        deployment=deployment,
                        replicas=new_replicas
                    )
                    
                    return {
                        "success": True,
                        "action": "auto_scaled",
                        "deployment": deployment,
                        "old_replicas": current_replicas,
                        "new_replicas": new_replicas,
                        "reason": "Not all pods ready",
                        "scale_result": scale_result
                    }
            
            return {
                "success": True,
                "action": "no_scaling_needed",
                "deployment": deployment,
                "replicas": current_replicas,
                "ready": ready_replicas
            }
        
        except Exception as e:
            logger.error(f"Error auto-scaling: {e}", exc_info=True)
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
