"""
Security Auto-Remediation Engine
Detects and fixes common security issues automatically
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SecurityEngine:
    """Engine for security auto-remediation"""
    
    def __init__(self):
        self.security_checks = [
            "pod_running_as_root",
            "missing_resource_limits",
            "privileged_containers",
            "host_network_access",
            "insecure_capabilities"
        ]
    
    def scan_pod_security(self, pod_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan pod for security issues
        Returns: {"issues": [], "recommendations": []}
        """
        issues = []
        recommendations = []
        
        containers = pod_spec.get("spec", {}).get("containers", [])
        
        for container in containers:
            container_name = container.get("name", "unknown")
            security_context = container.get("securityContext", {})
            
            # Check 1: Running as root
            run_as_non_root = security_context.get("runAsNonRoot")
            if not run_as_non_root:
                issues.append({
                    "type": "running_as_root",
                    "severity": "high",
                    "container": container_name,
                    "description": "Container may be running as root user"
                })
                recommendations.append({
                    "issue": "running_as_root",
                    "container": container_name,
                    "fix": "Set securityContext.runAsNonRoot: true and runAsUser: 1000"
                })
            
            # Check 2: Missing resource limits
            resources = container.get("resources", {})
            limits = resources.get("limits", {})
            
            if not limits.get("cpu") or not limits.get("memory"):
                issues.append({
                    "type": "missing_resource_limits",
                    "severity": "medium",
                    "container": container_name,
                    "description": "Missing CPU or memory limits"
                })
                recommendations.append({
                    "issue": "missing_resource_limits",
                    "container": container_name,
                    "fix": "Add resources.limits.cpu and resources.limits.memory"
                })
            
            # Check 3: Privileged mode
            if security_context.get("privileged"):
                issues.append({
                    "type": "privileged_container",
                    "severity": "critical",
                    "container": container_name,
                    "description": "Container running in privileged mode"
                })
                recommendations.append({
                    "issue": "privileged_container",
                    "container": container_name,
                    "fix": "Remove securityContext.privileged or set to false"
                })
            
            # Check 4: Capabilities
            capabilities = security_context.get("capabilities", {})
            if not capabilities.get("drop") or "ALL" not in capabilities.get("drop", []):
                issues.append({
                    "type": "insecure_capabilities",
                    "severity": "medium",
                    "container": container_name,
                    "description": "Not dropping all Linux capabilities"
                })
                recommendations.append({
                    "issue": "insecure_capabilities",
                    "container": container_name,
                    "fix": "Set securityContext.capabilities.drop: [ALL]"
                })
        
        # Check pod-level security
        pod_security = pod_spec.get("spec", {}).get("securityContext", {})
        host_network = pod_spec.get("spec", {}).get("hostNetwork", False)
        
        if host_network:
            issues.append({
                "type": "host_network_access",
                "severity": "high",
                "description": "Pod has access to host network"
            })
            recommendations.append({
                "issue": "host_network_access",
                "fix": "Remove spec.hostNetwork or set to false"
            })
        
        return {
            "issues_found": len(issues),
            "issues": issues,
            "recommendations": recommendations,
            "severity_summary": self._count_by_severity(issues)
        }
    
    def _count_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in issues:
            severity = issue.get("severity", "low")
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def generate_security_patch(
        self,
        pod_name: str,
        namespace: str,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate YAML patch to fix security issues
        """
        patches = []
        
        for issue in issues:
            issue_type = issue.get("type")
            container_name = issue.get("container")
            
            if issue_type == "running_as_root":
                patches.append({
                    "op": "add",
                    "path": f"/spec/containers/{container_name}/securityContext/runAsNonRoot",
                    "value": True
                })
                patches.append({
                    "op": "add",
                    "path": f"/spec/containers/{container_name}/securityContext/runAsUser",
                    "value": 1000
                })
            
            elif issue_type == "missing_resource_limits":
                patches.append({
                    "op": "add",
                    "path": f"/spec/containers/{container_name}/resources/limits",
                    "value": {
                        "cpu": "500m",
                        "memory": "512Mi"
                    }
                })
            
            elif issue_type == "privileged_container":
                patches.append({
                    "op": "replace",
                    "path": f"/spec/containers/{container_name}/securityContext/privileged",
                    "value": False
                })
            
            elif issue_type == "insecure_capabilities":
                patches.append({
                    "op": "add",
                    "path": f"/spec/containers/{container_name}/securityContext/capabilities",
                    "value": {
                        "drop": ["ALL"]
                    }
                })
        
        return {
            "pod": pod_name,
            "namespace": namespace,
            "patches": patches,
            "patch_count": len(patches),
            "note": "These patches can be applied with kubectl patch"
        }
    
    def auto_fix_security_issue(
        self,
        namespace: str,
        pod_name: str,
        issue_type: str
    ) -> Dict[str, Any]:
        """
        Automatically fix a specific security issue
        NOTE: This is a simulation - actual implementation would apply kubectl patch
        """
        logger.info(f"AUTO-FIX: Fixing {issue_type} for pod {pod_name} in {namespace}")
        
        fixes = {
            "running_as_root": "Applied runAsNonRoot: true and runAsUser: 1000",
            "missing_resource_limits": "Applied CPU/Memory limits",
            "privileged_container": "Removed privileged mode",
            "insecure_capabilities": "Dropped all Linux capabilities",
            "host_network_access": "Disabled host network access"
        }
        
        if issue_type not in fixes:
            return {
                "success": False,
                "error": f"Unknown issue type: {issue_type}"
            }
        
        return {
            "success": True,
            "action": "security_auto_fix",
            "issue_type": issue_type,
            "pod": pod_name,
            "namespace": namespace,
            "fix_applied": fixes[issue_type],
            "note": "Pod will be recreated with new security settings"
        }


# Global security engine instance
security_engine = SecurityEngine()
