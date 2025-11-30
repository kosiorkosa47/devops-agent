"""
Predictive Operations Engine
Analyzes trends and predicts potential issues before they occur
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class PredictiveEngine:
    """
    Engine for predictive operations - analyzes trends and predicts issues
    """
    
    def __init__(self):
        # Store recent metrics (in production, use time-series database)
        self.metrics_history = {}
        self.max_history_size = 100
        
    def record_pod_metrics(self, namespace: str, pod_name: str, metrics: Dict[str, Any]):
        """Record pod metrics for trend analysis"""
        key = f"{namespace}/{pod_name}"
        
        if key not in self.metrics_history:
            self.metrics_history[key] = deque(maxlen=self.max_history_size)
        
        metrics_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": metrics.get("cpu", "0m"),
            "memory": metrics.get("memory", "0Mi"),
            "restart_count": metrics.get("restart_count", 0)
        }
        
        self.metrics_history[key].append(metrics_entry)
        
    def predict_resource_exhaustion(
        self,
        namespace: str,
        pod_name: str,
        lookahead_hours: int = 3
    ) -> Dict[str, Any]:
        """
        Predict if pod will run out of resources in the next N hours
        Uses simple trend analysis
        """
        key = f"{namespace}/{pod_name}"
        
        if key not in self.metrics_history or len(self.metrics_history[key]) < 3:
            return {
                "prediction": "insufficient_data",
                "message": "Need more data points for prediction"
            }
        
        history = list(self.metrics_history[key])
        
        # Simplified analysis - check if restarts are increasing
        restart_counts = [h.get("restart_count", 0) for h in history]
        
        if len(restart_counts) >= 3:
            recent_restarts = restart_counts[-3:]
            if recent_restarts[-1] > recent_restarts[0]:
                return {
                    "prediction": "warning",
                    "type": "increasing_restarts",
                    "pod": pod_name,
                    "namespace": namespace,
                    "message": f"Pod restart count increasing: {recent_restarts}",
                    "recommendation": "Check pod logs and resource limits",
                    "urgency": "medium",
                    "estimated_time_to_failure": f"{lookahead_hours} hours"
                }
        
        # Check memory trend (simplified)
        memory_values = []
        for h in history:
            mem_str = h.get("memory", "0Mi")
            try:
                # Extract numeric value (very simplified)
                mem_val = float(mem_str.replace("Mi", "").replace("Gi", "000"))
                memory_values.append(mem_val)
            except:
                pass
        
        if len(memory_values) >= 5:
            # Simple trend: if last 3 values consistently higher than first 3
            early_avg = sum(memory_values[:3]) / 3
            late_avg = sum(memory_values[-3:]) / 3
            
            if late_avg > early_avg * 1.5:  # 50% increase
                return {
                    "prediction": "warning",
                    "type": "memory_trend_increase",
                    "pod": pod_name,
                    "namespace": namespace,
                    "message": f"Memory usage increasing trend detected",
                    "early_avg_mb": round(early_avg, 2),
                    "late_avg_mb": round(late_avg, 2),
                    "increase_percent": round((late_avg / early_avg - 1) * 100, 1),
                    "recommendation": "Consider increasing memory limits or investigating memory leak",
                    "urgency": "medium",
                    "estimated_time_to_exhaustion": f"{lookahead_hours} hours"
                }
        
        return {
            "prediction": "ok",
            "pod": pod_name,
            "namespace": namespace,
            "message": "No issues predicted in the near term"
        }
    
    def suggest_preemptive_actions(
        self,
        namespace: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze all pods in namespace and suggest preemptive actions
        """
        suggestions = []
        
        for key, history in self.metrics_history.items():
            if not key.startswith(f"{namespace}/"):
                continue
            
            pod_name = key.split("/")[1]
            
            # Get prediction
            prediction = self.predict_resource_exhaustion(namespace, pod_name)
            
            if prediction["prediction"] == "warning":
                suggestions.append({
                    "pod": pod_name,
                    "issue": prediction["type"],
                    "action": "preemptive_action",
                    "recommendation": prediction["recommendation"],
                    "urgency": prediction["urgency"]
                })
        
        return suggestions
    
    def identify_failure_patterns(
        self,
        namespace: str
    ) -> Dict[str, Any]:
        """
        Identify patterns in failures that might indicate systemic issues
        """
        patterns = {
            "frequent_restarts": [],
            "consistent_failures": [],
            "time_based_patterns": []
        }
        
        for key, history in self.metrics_history.items():
            if not key.startswith(f"{namespace}/"):
                continue
            
            pod_name = key.split("/")[1]
            restart_counts = [h.get("restart_count", 0) for h in history]
            
            # Check for frequent restarts
            if len(restart_counts) >= 5:
                if restart_counts[-1] > 3:  # More than 3 restarts
                    patterns["frequent_restarts"].append({
                        "pod": pod_name,
                        "restart_count": restart_counts[-1],
                        "severity": "high" if restart_counts[-1] > 10 else "medium"
                    })
        
        return {
            "namespace": namespace,
            "patterns_found": patterns,
            "analysis_time": datetime.utcnow().isoformat(),
            "recommendations": self._generate_pattern_recommendations(patterns)
        }
    
    def _generate_pattern_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on identified patterns"""
        recommendations = []
        
        if patterns["frequent_restarts"]:
            recommendations.append(
                f"🔴 {len(patterns['frequent_restarts'])} pods with frequent restarts detected. "
                f"Investigate resource limits, liveness probes, and application stability."
            )
        
        if not any(patterns.values()):
            recommendations.append("✅ No concerning patterns detected. System appears healthy.")
        
        return recommendations
    
    def predict_scaling_needs(
        self,
        namespace: str,
        deployment: str,
        current_replicas: int
    ) -> Dict[str, Any]:
        """
        Predict if deployment will need scaling soon
        """
        # Simplified prediction based on pod health
        pods_key_pattern = f"{namespace}/"
        
        unhealthy_count = 0
        total_pods = 0
        
        for key in self.metrics_history:
            if key.startswith(pods_key_pattern):
                total_pods += 1
                history = self.metrics_history[key]
                if history:
                    latest = list(history)[-1]
                    if latest.get("restart_count", 0) > 2:
                        unhealthy_count += 1
        
        if total_pods == 0:
            return {
                "prediction": "insufficient_data",
                "message": "No pod metrics available"
            }
        
        unhealthy_ratio = unhealthy_count / total_pods
        
        if unhealthy_ratio > 0.3:  # More than 30% unhealthy
            recommended_replicas = min(current_replicas + 2, 20)
            return {
                "prediction": "scale_up_recommended",
                "deployment": deployment,
                "namespace": namespace,
                "current_replicas": current_replicas,
                "recommended_replicas": recommended_replicas,
                "reason": f"{unhealthy_ratio*100:.1f}% of pods showing issues",
                "urgency": "high",
                "action": "Consider scaling up to handle load better"
            }
        
        elif unhealthy_ratio == 0 and current_replicas > 2:
            # All healthy, might be over-provisioned
            recommended_replicas = max(current_replicas - 1, 2)
            return {
                "prediction": "scale_down_possible",
                "deployment": deployment,
                "namespace": namespace,
                "current_replicas": current_replicas,
                "recommended_replicas": recommended_replicas,
                "reason": "All pods healthy, may be over-provisioned",
                "urgency": "low",
                "action": "Consider scaling down to save resources"
            }
        
        return {
            "prediction": "no_scaling_needed",
            "deployment": deployment,
            "current_replicas": current_replicas,
            "message": "Current replica count appears optimal"
        }


# Global predictive engine instance
predictive_engine = PredictiveEngine()
