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

resource "azurerm_resource_group" "test_rg" {
  name     = "rg-tf-test-deployment"
  location = "Southeast Asia"
}

resource "azurerm_virtual_network" "test_vnet" {
  name                = "vnet-test"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.test_rg.location
  resource_group_name = azurerm_resource_group.test_rg.name
}

resource "azurerm_subnet" "test_subnet" {
  name                 = "snet-test"
  resource_group_name  = azurerm_resource_group.test_rg.name
  virtual_network_name = azurerm_virtual_network.test_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "test_pip" {
  name                = "pip-test"
  location            = azurerm_resource_group.test_rg.location
  resource_group_name = azurerm_resource_group.test_rg.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_security_group" "test_nsg" {
  name                = "nsg-test"
  location            = azurerm_resource_group.test_rg.location
  resource_group_name = azurerm_resource_group.test_rg.name

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  security_rule {
    name                       = "AllowSSH"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "test_nic" {
  name                = "nic-test"
  location            = azurerm_resource_group.test_rg.location
  resource_group_name = azurerm_resource_group.test_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.test_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.test_pip.id
  }
}

resource "azurerm_network_interface_security_group_association" "test_nic_nsg" {
  network_interface_id      = azurerm_network_interface.test_nic.id
  network_security_group_id = azurerm_network_security_group.test_nsg.id
}

resource "tls_private_key" "example_ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "azurerm_linux_virtual_machine" "test_vm" {
  name                = "vm-test-nginx"
  resource_group_name = azurerm_resource_group.test_rg.name
  location            = azurerm_resource_group.test_rg.location
  size                = "Standard_B2s"
  admin_username      = "adminuser"
  
  network_interface_ids = [
    azurerm_network_interface.test_nic.id,
  ]

  admin_ssh_key {
    username   = "adminuser"
    public_key = tls_private_key.example_ssh.public_key_openssh
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  custom_data = base64encode(<<-EOF
#!/bin/bash
apt-get update
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx
echo "<h1>Welcome to Nginx on Azure VM (Southeast Asia)</h1>" > /var/www/html/index.html
EOF
  )
}

output "public_ip_address" {
  value = azurerm_public_ip.test_pip.ip_address
}
