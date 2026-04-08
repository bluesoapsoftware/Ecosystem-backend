# database.tf - AWS RDS MySQL Database

# 1. RDS Subnet Group
# This defines a group of subnets (ideally private) for the RDS instance
resource "aws_db_subnet_group" "bluesoap_db_subnet_group" {
  name       = "bluesoap-db-subnet-group"
  subnet_ids = [aws_subnet.bluesoap_private_subnet_az1.id, aws_subnet.bluesoap_private_subnet_az2.id]
  description = "Private subnets for BlueSoap RDS instance"

  tags = {
    Name        = "bluesoap-db-subnet-group"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 2. RDS MySQL Database Instance
resource "aws_db_instance" "bluesoap_mysql_db" {
  allocated_storage    = 20
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.micro" # Cost-effective instance for development/small production
  db_name              = "bluesoap_db" # Default database name
  username             = var.db_username # Securely managed variable
  password             = var.db_password # Securely managed variable
  db_subnet_group_name = aws_db_subnet_group.bluesoap_db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.bluesoap_sg_rds.id]
  skip_final_snapshot  = true # Set to false in production for backups
  publicly_accessible  = false # Crucial for security - keep database private
  multi_az             = true # For high availability
  identifier           = "bluesoap-ecosystem"
  port                 = 3306

  tags = {
    Name        = "bluesoap-mysql-db"
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# Output RDS Endpoint and Port
output "rds_endpoint" {
  description = "The address of the RDS instance."
  value       = aws_db_instance.bluesoap_mysql_db.address
}

output "rds_port" {
  description = "The port of the RDS instance."
  value       = aws_db_instance.bluesoap_mysql_db.port
}
