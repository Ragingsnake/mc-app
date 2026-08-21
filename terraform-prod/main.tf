terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# 1. Resource Group
resource "azurerm_resource_group" "prod_rg" {
  name     = "rg-minecraft-story-prod"
  location = "Southeast Asia"
}

# 2. AKS Cluster
resource "azurerm_kubernetes_cluster" "prod_aks" {
  name                = "aks-mc-story-prod"
  location            = azurerm_resource_group.prod_rg.location
  resource_group_name = azurerm_resource_group.prod_rg.name
  dns_prefix          = "mcstoryaks"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2s_v3"
  }

  identity {
    type = "SystemAssigned"
  }
}

# 3. Public IP for the Frontend in the AKS-managed node resource group
resource "azurerm_public_ip" "frontend_ip" {
  name                = "pip-frontend-ingress"
  resource_group_name = azurerm_kubernetes_cluster.prod_aks.node_resource_group
  location            = azurerm_resource_group.prod_rg.location
  allocation_method   = "Static"
  sku                 = "Standard"

  # Free Azure subdomain: mc-story-thing.southeastasia.cloudapp.azure.com
  domain_name_label = "mc-story-thing"

  depends_on = [azurerm_kubernetes_cluster.prod_aks]
}

# Outputs used by the Helm deploy job
output "aks_name" {
  value = azurerm_kubernetes_cluster.prod_aks.name
}

output "resource_group_name" {
  value = azurerm_resource_group.prod_rg.name
}

output "frontend_ip" {
  value = azurerm_public_ip.frontend_ip.ip_address
}

output "frontend_fqdn" {
  value = azurerm_public_ip.frontend_ip.fqdn
}
