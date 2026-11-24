variable "environment" {
  description = "Short environment name used in resource names, for example dev or prod."
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "West Europe"
}

variable "domain_name" {
  description = "Public DNS name pointing at the VM's IP. Caddy gets a TLS certificate for it automatically."
  type        = string
}

variable "admin_cidr" {
  description = "Address range allowed to reach SSH, for example your office IP as 203.0.113.10/32."
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && !contains(["0.0.0.0/0", "*", "Internet", "Any"], var.admin_cidr)
    error_message = "admin_cidr must be a specific CIDR range, never the whole internet."
  }
}

variable "ssh_public_key" {
  description = "Public key for the VM admin user."
  type        = string
}

variable "repo_url" {
  description = "Git repository the VM builds the app from."
  type        = string
  default     = "https://github.com/munuhee/sales-and-inventory-management.git"
}

variable "repo_ref" {
  description = "Branch or tag to deploy."
  type        = string
  default     = "main"
}
