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
    def get_security_tools() -> List[Dict[str, Any]]:
        """Security auto-remediation tools"""
        return [
            {
                "name": "scan_pod_security",
                "description": "🔒 SECURITY: Scan pod for security issues (root user, missing limits, privileged mode, etc.)",
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
                "name": "auto_fix_security_issue",
                "description": "🔒 SECURITY AUTO-FIX: Automatically fix a specific security issue in a pod (dangerous - requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod_name": {"type": "string"},
                        "issue_type": {
                            "type": "string",
                            "description": "Type of issue to fix (e.g., 'running_as_root', 'missing_resource_limits')"
                        }
                    },
                    "required": ["namespace", "pod_name", "issue_type"]
                }
            }
        ]
    
    @staticmethod
    def get_system_tools() -> List[Dict[str, Any]]:
        """Infrastructure installation and management tools"""
        return [
            {
                "name": "install_minikube",
                "description": "Install Minikube for local Kubernetes cluster. Works on Windows, Linux, and macOS. Automatically installs dependencies (Chocolatey on Windows).",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "install_kubectl",
                "description": "Install kubectl CLI tool for Kubernetes management. Required for interacting with Kubernetes clusters.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "start_minikube",
                "description": "Start Minikube Kubernetes cluster. Creates a single-node cluster for local development. Requires Minikube to be installed first.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "driver": {
                            "type": "string",
                            "description": "Driver to use (docker, hyperv, virtualbox). Default: docker",
                            "enum": ["docker", "hyperv", "virtualbox", "vmware"]
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "stop_minikube",
                "description": "Stop running Minikube cluster. Preserves cluster state for later restart.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_cluster_status",
                "description": "Get status of all Kubernetes clusters and tools. Shows what's installed, running, and connected.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "check_tool_installed",
                "description": "Check if a specific tool is installed on the system (kubectl, minikube, docker, etc.)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the tool to check (e.g., kubectl, minikube, docker, helm)"
                        }
                    },
                    "required": ["tool_name"]
                }
            },
            {
                "name": "execute_powershell_command",
                "description": "⚠️ Execute a PowerShell command on the Windows system. Use for system administration, file operations, and Windows-specific tasks. DANGEROUS - requires approval.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "PowerShell command to execute (e.g., 'Get-Process', 'Get-Service', 'Test-Path')"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 300, max: 600)"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "execute_cmd_command",
                "description": "⚠️ Execute a CMD/batch command on Windows. Use for simple file operations, directory listings, and legacy Windows commands. DANGEROUS - requires approval.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "CMD command to execute (e.g., 'dir', 'type file.txt', 'echo hello')"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 300, max: 600)"
                        }
                    },
                    "required": ["command"]
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
            ToolDefinitions.get_predictive_tools() +
            ToolDefinitions.get_security_tools() +
            ToolDefinitions.get_system_tools()
        )
    
    @staticmethod
    def is_dangerous_operation(tool_name: str) -> bool:
        """Check if a tool requires approval"""
        # Command execution is ALWAYS dangerous - requires approval
        if tool_name in ["execute_powershell_command", "execute_cmd_command"]:
            return True
        
        # Installation tools are considered safe (only install, don't modify existing)
        safe_install_tools = ["install_minikube", "install_kubectl", "check_tool_installed", "get_cluster_status"]
        if tool_name in safe_install_tools:
            return False
        
        dangerous_keywords = ["delete", "destroy", "scale", "apply", "deploy", "restart", "kill", "start", "stop"]
        return any(keyword in tool_name.lower() for keyword in dangerous_keywords)
    
    @staticmethod
    def get_tool_by_name(tool_name: str) -> Dict[str, Any]:
        """Get tool definition by name"""
        all_tools = ToolDefinitions.get_all_tools()
        for tool in all_tools:
            if tool["name"] == tool_name:
                return tool
        raise ValueError(f"Tool not found: {tool_name}")
