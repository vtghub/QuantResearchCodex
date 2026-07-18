variable "resource_group_name" {
  type        = string
  description = "Azure resource group for QuantResearchCodex."
  default     = "rg-quantresearchcodex"
}

variable "location" {
  type        = string
  description = "Azure region."
  default     = "eastus"
}
