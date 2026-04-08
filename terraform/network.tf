# network.tf - AWS VPC and Networking Resources

# 1. Main VPC for BlueSoap Ecosystem
resource "aws_vpc" "bluesoap_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "bluesoap-vpc"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 2. Internet Gateway for Public Internet Access
resource "aws_internet_gateway" "bluesoap_igw" {
  vpc_id = aws_vpc.bluesoap_vpc.id

  tags = {
    Name        = "bluesoap-igw"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 3. Elastic IP for NAT Gateway (required for a public IP for NAT)
resource "aws_eip" "nat_gateway_eip" {
  vpc        = true # Allocate an EIP for use in a VPC

  tags = {
    Name        = "bluesoap-nat-eip"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 4. NAT Gateway for Private Subnet Outbound Internet Access
resource "aws_nat_gateway" "bluesoap_nat_gateway" {
  allocation_id = aws_eip.nat_gateway_eip.id
  subnet_id     = aws_subnet.bluesoap_public_subnet_az1.id # Deploy in a public subnet

  tags = {
    Name        = "bluesoap-nat-gw"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }

  # Ensure the NAT Gateway is created after the Internet Gateway
  depends_on = [aws_internet_gateway.bluesoap_igw]
}


# 5. Public Subnets (for Load Balancers, Bastion Hosts, NAT Gateways)
# We'll create two public subnets for high availability across two AZs
resource "aws_subnet" "bluesoap_public_subnet_az1" {
  vpc_id                  = aws_vpc.bluesoap_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a" # e.g., us-east-2a
  map_public_ip_on_launch = true # Instances in this subnet get a public IP by default

  tags = {
    Name        = "bluesoap-public-az1"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

resource "aws_subnet" "bluesoap_public_subnet_az2" {
  vpc_id                  = aws_vpc.bluesoap_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b" # e.g., us-east-2b
  map_public_ip_on_launch = true

  tags = {
    Name        = "bluesoap-public-az2"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 6. Private Subnets (for Application Servers, Databases)
# We'll create two private subnets for high availability across two AZs
resource "aws_subnet" "bluesoap_private_subnet_az1" {
  vpc_id            = aws_vpc.bluesoap_vpc.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name        = "bluesoap-private-az1"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

resource "aws_subnet" "bluesoap_private_subnet_az2" {
  vpc_id            = aws_vpc.bluesoap_vpc.id
  cidr_block        = "10.0.12.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name        = "bluesoap-private-az2"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 7. Route Table for Public Subnets
resource "aws_route_table" "bluesoap_public_rt" {
  vpc_id = aws_vpc.bluesoap_vpc.id

  route {
    cidr_block = "0.0.0.0/0" # Allow all outbound traffic
    gateway_id = aws_internet_gateway.bluesoap_igw.id
  }

  tags = {
    Name        = "bluesoap-public-rt"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 8. Route Table Associations for Public Subnets
resource "aws_route_table_association" "bluesoap_public_rt_assoc_az1" {
  subnet_id      = aws_subnet.bluesoap_public_subnet_az1.id
  route_table_id = aws_route_table.bluesoap_public_rt.id
}

resource "aws_route_table_association" "bluesoap_public_rt_assoc_az2" {
  subnet_id      = aws_subnet.bluesoap_public_subnet_az2.id
  route_table_id = aws_route_table.bluesoap_public_rt.id
}

# 9. Route Table for Private Subnets
resource "aws_route_table" "bluesoap_private_rt" {
  vpc_id = aws_vpc.bluesoap_vpc.id

  route {
    cidr_block     = "0.0.0.0/0" # Allow all outbound traffic
    nat_gateway_id = aws_nat_gateway.bluesoap_nat_gateway.id
  }

  tags = {
    Name        = "bluesoap-private-rt"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 10. Route Table Associations for Private Subnets
resource "aws_route_table_association" "bluesoap_private_rt_assoc_az1" {
  subnet_id      = aws_subnet.bluesoap_private_subnet_az1.id
  route_table_id = aws_route_table.bluesoap_private_rt.id
}

resource "aws_route_table_association" "bluesoap_private_rt_assoc_az2" {
  subnet_id      = aws_subnet.bluesoap_private_subnet_az2.id
  route_table_id = aws_route_table.bluesoap_private_rt.id
}

# 11. Security Group for Management (SSH access to bastion/management servers)
resource "aws_security_group" "bluesoap_sg_management" {
  name        = "bluesoap-sg-management"
  description = "Allow SSH from anywhere (TEMPORARY - RESTRICT THIS SOON)" # TEMPORARY
  vpc_id      = aws_vpc.bluesoap_vpc.id

  ingress {
    description = "SSH from everywhere (TEMPORARY)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: This should be restricted to known IPs!
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "bluesoap-sg-management"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 12. Security Group for FastAPI Backend
resource "aws_security_group" "bluesoap_sg_fastapi" {
  name        = "bluesoap-sg-fastapi"
  description = "Allow inbound FastAPI traffic from NGINX and SSH from management SG."
  vpc_id      = aws_vpc.bluesoap_vpc.id

  ingress {
    description = "Allow FastAPI port from NGINX Security Group"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    security_groups = [aws_security_group.bluesoap_sg_nginx.id]
  }

  ingress {
    description     = "SSH from Management Security Group"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bluesoap_sg_management.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "bluesoap-sg-fastapi"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 13. Security Group for NGINX Reverse Proxy
resource "aws_security_group" "bluesoap_sg_nginx" {
  name        = "bluesoap-sg-nginx"
  description = "Allow HTTP/HTTPS from internet, and SSH from management SG."
  vpc_id      = aws_vpc.bluesoap_vpc.id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description     = "SSH from Management Security Group"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bluesoap_sg_management.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "bluesoap-sg-nginx"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 14. Security Group for RDS Database
resource "aws_security_group" "bluesoap_sg_rds" {
  name        = "bluesoap-sg-rds"
  description = "Allow MySQL traffic from FastAPI Security Group."
  vpc_id      = aws_vpc.bluesoap_vpc.id

  ingress {
    description = "Allow MySQL from FastAPI Security Group"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    security_groups = [aws_security_group.bluesoap_sg_fastapi.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "bluesoap-sg-rds"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# Output VPC and Subnet IDs
output "vpc_id" {
  description = "The ID of the main VPC."
  value       = aws_vpc.bluesoap_vpc.id
}

output "public_subnet_ids" {
  description = "List of IDs of the public subnets."
  value       = [aws_subnet.bluesoap_public_subnet_az1.id, aws_subnet.bluesoap_public_subnet_az2.id]
}

output "private_subnet_ids" {
  description = "List of IDs of the private subnets."
  value       = [aws_subnet.bluesoap_private_subnet_az1.id, aws_subnet.bluesoap_private_subnet_az2.id]
}

output "sg_management_id" {
  description = "The ID of the management security group."
  value       = aws_security_group.bluesoap_sg_management.id
}

output "sg_fastapi_id" {
  description = "The ID of the FastAPI security group."
  value       = aws_security_group.bluesoap_sg_fastapi.id
}

output "sg_nginx_id" {
  description = "The ID of the NGINX security group."
  value       = aws_security_group.bluesoap_sg_nginx.id
}

output "sg_rds_id" {
  description = "The ID of the RDS security group."
  value       = aws_security_group.bluesoap_sg_rds.id
}
