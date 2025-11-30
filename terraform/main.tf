# Main Terraform Configuration
# DevOps Agent Infrastructure as Code

terraform {
  required_version = ">= 1.6"
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
  
  # Backend for state storage
  backend "s3" {
    bucket = "terraform-state"
    key    = "devops-agent/terraform.tfstate"
    region = "us-east-1"
    
    # MinIO S3-compatible
    endpoint = "minio.yourdomain.com"
    skip_credentials_validation = true
    skip_metadata_api_check = true
    skip_region_validation = true
    force_path_style = true
  }
}

# Provider configuration
provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# Variables
variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "domain" {
  description = "Base domain for applications"
  type        = string
  default     = "yourdomain.com"
}

# Modules
module "namespaces" {
  source = "./modules/namespaces"
}

module "monitoring" {
  source      = "./modules/monitoring"
  domain      = var.domain
  environment = var.environment
  
  depends_on = [module.namespaces]
}

module "storage" {
  source      = "./modules/storage"
  environment = var.environment
  
  depends_on = [module.namespaces]
}

module "applications" {
  source      = "./modules/applications"
  domain      = var.domain
  environment = var.environment
  
  depends_on = [module.storage, module.monitoring]
}

# Outputs
output "grafana_url" {
  value = "https://grafana.${var.domain}"
}

output "minio_console_url" {
  value = "https://minio.${var.domain}"
}

output "application_url" {
  value = "https://${var.domain}"
}
