"""
DevOps Tools Definitions for Claude Function Calling
All available tools that ATLAS agent can execute
"""
from typing import List, Dict, Any


class ToolDefinitions:
    """Central registry of all available tools"""
    
    # Tool categories
    SAFE_OPERATIONS = ["read", "get", "list", "describe", "logs", "status", "analyze", "check"]
    DANGEROUS_OPERATIONS = ["delete", "destroy", "apply", "deploy", "scale", "restart", "kill", "auto_restart", "auto_scale"]
    
    @staticmethod
    def get_kubernetes_tools() -> List[Dict[str, Any]]:
        """Kubernetes operations tools"""
        return [
            {
                "name": "kubectl_get_pods",
                "description": "List all pods in a namespace or across all namespaces. Returns pod names, status, age, and resource usage.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace (optional, all namespaces if not provided)"
                        },
                        "label_selector": {
                            "type": "string",
                            "description": "Label selector to filter pods (e.g., 'app=backend')"
                        }
                    }
                }
            },
            {
                "name": "kubectl_get_pod_logs",
                "description": "Get logs from a specific pod. Can tail last N lines.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace"
                        },
                        "pod_name": {
                            "type": "string",
                            "description": "Name of the pod"
                        },
                        "container": {
                            "type": "string",
                            "description": "Container name (optional if pod has single container)"
                        },
                        "tail_lines": {
                            "type": "integer",
                            "description": "Number of lines to return from the end (default: 100)"
                        },
                        "follow": {
                            "type": "boolean",
                            "description": "Follow logs in real-time (default: false)"
                        }
                    },
                    "required": ["namespace", "pod_name"]
                }
            },
            {
                "name": "kubectl_describe_pod",
                "description": "Get detailed information about a pod including events, conditions, and resource usage.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod_name": {"type": "string"}
                    },
                    "required": ["namespace", "pod_name"]
                }
            },
            {
                "name": "kubectl_get_deployments",
                "description": "List all deployments in a namespace",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"}
                    }
                }
            },
            {
                "name": "kubectl_scale_deployment",
                "description": "⚠️ DANGEROUS: Scale a deployment to specified number of replicas",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "deployment_name": {"type": "string"},
                        "replicas": {
                            "type": "integer",
                            "description": "Number of replicas (0-50)"
                        }
                    },
                    "required": ["namespace", "deployment_name", "replicas"]
                }
            },
            {
                "name": "kubectl_delete_pod",
                "description": "⚠️ DANGEROUS: Delete a pod (will be recreated by deployment/statefulset)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod_name": {"type": "string"}
                    },
                    "required": ["namespace", "pod_name"]
                }
            },
            {
                "name": "kubectl_get_events",
                "description": "Get recent Kubernetes events (useful for debugging)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Namespace (optional, all if not provided)"
                        },
                        "resource_name": {
                            "type": "string",
                            "description": "Filter events for specific resource"
                        }
                    }
                }
            },
            {
                "name": "kubectl_top_pods",
                "description": "Get current CPU and memory usage of pods",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"}
                    }
                }
            },
            {
                "name": "analyze_resource_efficiency",
                "description": "🔍 ANALYSIS: Analyze resource efficiency for pods - identifies over/under-provisioned resources and suggests optimizations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Namespace to analyze (default: default)"
                        }
                    }
                }
            },
            {
                "name": "auto_restart_pod",
                "description": "🔧 SELF-HEALING: Automatically restart a failed pod by deleting it (will be recreated by controller). This is a destructive operation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod_name": {"type": "string"}
                    },
                    "required": ["namespace", "pod_name"]
                }
            },
            {
                "name": "auto_scale_if_needed",
                "description": "🔧 SELF-HEALING: Automatically scale deployment if pods are not ready. Intelligently adds replicas if needed (up to max).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "deployment": {"type": "string"},
                        "max_replicas": {
                            "type": "integer",
                            "description": "Maximum replicas to scale to (default: 10)"
                        }
                    },
                    "required": ["namespace", "deployment"]
                }
            }
        ]
    
    @staticmethod
    def get_docker_tools() -> List[Dict[str, Any]]:
        """Docker operations tools"""
        return [
            {
                "name": "docker_ps",
                "description": "List running containers",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "Show all containers (including stopped)"
                        }
                    }
                }
            },
            {
                "name": "docker_logs",
                "description": "Get logs from a container",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "container_id": {"type": "string"},
                        "tail": {"type": "integer", "description": "Number of lines"}
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "docker_inspect",
                "description": "Get detailed information about a container",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "container_id": {"type": "string"}
                    },
                    "required": ["container_id"]
                }
            }
        ]
    
    @staticmethod
    def get_git_tools() -> List[Dict[str, Any]]:
        """Git operations tools"""
        return [
            {
                "name": "git_status",
                "description": "Get git repository status",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Path to repository"}
                    }
                }
            },
            {
                "name": "git_log",
                "description": "Get recent commit history",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string"},
                        "max_count": {"type": "integer", "description": "Number of commits (default: 10)"}
                    }
                }
            },
            {
                "name": "git_diff",
                "description": "Show changes in working directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string"},
                        "cached": {"type": "boolean", "description": "Show staged changes"}
                    }
                }
            }
        ]
    
    @staticmethod
    def get_monitoring_tools() -> List[Dict[str, Any]]:
        """Monitoring and observability tools"""
        return [
            {
                "name": "prometheus_query",
                "description": "Execute a Prometheus query",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "PromQL query (e.g., 'up', 'rate(http_requests_total[5m])')"
                        },
                        "time": {
                            "type": "string",
                            "description": "Evaluation time (optional, defaults to now)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "check_pod_health",
                "description": "Check if a pod is healthy (running, ready, no crashes)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod_name": {"type": "string"}
                    },
                    "required": ["namespace", "pod_name"]
                }
            },
            {
                "name": "analyze_error_logs",
                "description": "Analyze pod logs for errors and provide summary",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod_name": {"type": "string"}
                    },
                    "required": ["namespace", "pod_name"]
                }
            }
        ]
    
    @staticmethod
    def get_predictive_tools() -> List[Dict[str, Any]]:
        """Predictive operations tools"""
        return [
            {
                "name": "predict_resource_exhaustion",
                "description": "🔮 PREDICTIVE: Predict if pod will run out of resources in the next few hours based on trend analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod_name": {"type": "string"},
                        "lookahead_hours": {
                            "type": "integer",
                            "description": "Hours to look ahead (default: 3)"
                        }
                    },
                    "required": ["namespace", "pod_name"]
                }
            },
            {
                "name": "suggest_preemptive_actions",
                "description": "🔮 PREDICTIVE: Analyze namespace and suggest preemptive actions to prevent issues",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"}
                    },
                    "required": ["namespace"]
                }
            },
            {
                "name": "identify_failure_patterns",
                "description": "🔮 PREDICTIVE: Identify failure patterns that might indicate systemic issues",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"}
                    },
                    "required": ["namespace"]
                }
            },
            {
                "name": "predict_scaling_needs",
                "description": "🔮 PREDICTIVE: Predict if deployment will need scaling soon based on pod health trends",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "deployment": {"type": "string"},
                        "current_replicas": {"type": "integer"}
                    },
                    "required": ["namespace", "deployment", "current_replicas"]
                }
            }
        ]
    
    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """Get all available tools"""
        return (
            ToolDefinitions.get_kubernetes_tools() +
            ToolDefinitions.get_docker_tools() +
            ToolDefinitions.get_git_tools() +
            ToolDefinitions.get_monitoring_tools() +
            ToolDefinitions.get_predictive_tools()
        )
    
    @staticmethod
    def is_dangerous_operation(tool_name: str) -> bool:
        """Check if a tool requires approval"""
        dangerous_keywords = ["delete", "destroy", "scale", "apply", "deploy", "restart", "kill"]
        return any(keyword in tool_name.lower() for keyword in dangerous_keywords)
    
    @staticmethod
    def get_tool_by_name(tool_name: str) -> Dict[str, Any]:
        """Get tool definition by name"""
        all_tools = ToolDefinitions.get_all_tools()
        for tool in all_tools:
            if tool["name"] == tool_name:
                return tool
        raise ValueError(f"Tool not found: {tool_name}")
