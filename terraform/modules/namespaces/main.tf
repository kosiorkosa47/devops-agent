# Namespaces Module

resource "kubernetes_namespace" "namespaces" {
  for_each = toset([
    "production",
    "staging",
    "dev",
    "monitoring",
    "security",
    "storage",
    "data"
  ])
  
  metadata {
    name = each.value
    
    labels = {
      "environment" = each.value
      "managed-by"  = "terraform"
    }
    
    annotations = {
      "pod-security.kubernetes.io/enforce" = each.value == "production" ? "restricted" : "baseline"
      "pod-security.kubernetes.io/audit"   = "restricted"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}

resource "kubernetes_resource_quota" "namespace_quotas" {
  for_each = {
    production = {
      cpu_requests    = "20"
      cpu_limits      = "40"
      memory_requests = "40Gi"
      memory_limits   = "80Gi"
      pods            = "100"
    }
    staging = {
      cpu_requests    = "10"
      cpu_limits      = "20"
      memory_requests = "20Gi"
      memory_limits   = "40Gi"
      pods            = "50"
    }
    dev = {
      cpu_requests    = "5"
      cpu_limits      = "10"
      memory_requests = "10Gi"
      memory_limits   = "20Gi"
      pods            = "30"
    }
  }
  
  metadata {
    name      = "resource-quota"
    namespace = kubernetes_namespace.namespaces[each.key].metadata[0].name
  }
  
  spec {
    hard = {
      "requests.cpu"    = each.value.cpu_requests
      "limits.cpu"      = each.value.cpu_limits
      "requests.memory" = each.value.memory_requests
      "limits.memory"   = each.value.memory_limits
      pods              = each.value.pods
    }
  }
}

output "namespace_names" {
  value = [for ns in kubernetes_namespace.namespaces : ns.metadata[0].name]
}
