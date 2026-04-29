terraform {
  required_version = ">= 1.6.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

locals {
  project_name = "HybridAIAutomation"
  common_tags = {
    environment = var.environment
    owner       = "platform"
    project     = local.project_name
  }
}

variable "tenancy_ocid" {
  type        = string
  description = "OCI tenancy OCID."
}

variable "user_ocid" {
  type        = string
  description = "OCI user OCID."
}

variable "fingerprint" {
  type        = string
  description = "Fingerprint for the OCI API signing key."
}

variable "private_key_path" {
  type        = string
  description = "Path to the OCI private API key."
}

variable "region" {
  type        = string
  description = "OCI region."
  default     = "us-chicago-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment."
  default     = "dev"
}

output "project_name" {
  value = local.project_name
}

output "common_tags" {
  value = local.common_tags
}
