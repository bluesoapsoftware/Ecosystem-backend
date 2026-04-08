# client_projects.tf - AWS Resources for Client Projects

# --- Life on the Rock International ---

# 1. S3 Bucket for Static Website Hosting
resource "aws_s3_bucket" "lotr_website_bucket" {
  bucket = "lifeontherock.org" # Canonical domain name as bucket name

  tags = {
    Name        = "lifeontherock.org-website"
    Project     = "LifeOnTheRockInternational"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Client      = "JohnMoreland"
  }
}

# Enable S3 Static Website Hosting
resource "aws_s3_bucket_website_configuration" "lotr_website_config" {
  bucket = aws_s3_bucket.lotr_website_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# 2. S3 Bucket Policy to Allow CloudFront Access (OAI)
resource "aws_s3_bucket_policy" "lotr_bucket_policy" {
  bucket = aws_s3_bucket.lotr_website_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontAccess"
        Effect    = "Allow"
        Principal = {
          AWS = "${aws_cloudfront_origin_access_identity.lotr_oai.iam_arn}"
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.lotr_website_bucket.arn}/*"
      }
    ]
  })
}

# CloudFront Origin Access Identity (OAI) for S3 Bucket
resource "aws_cloudfront_origin_access_identity" "lotr_oai" {
  comment = "OAI for lifeontherock.org CloudFront distribution"
}

# 3. CloudFront Distribution for lifeontherock.org
resource "aws_cloudfront_distribution" "lotr_cdn" {
  origin {
    domain_name = aws_s3_bucket.lotr_website_bucket.bucket_regional_domain_name
    origin_id   = "S3-lifeontherock.org"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.lotr_oai.cloudfront_access_identity_path
    }
  }

  enabled         = true
  is_ipv6_enabled = true
  comment         = "CloudFront distribution for lifeontherock.org"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "S3-lifeontherock.org"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true # Use CloudFront's default SSL for now (requires custom cert later)
  }


  tags = {
    Name        = "lifeontherock.org-cdn"
    Project     = "LifeOnTheRockInternational"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Client      = "JohnMoreland"
  }
}

# 4. Route 53 DNS Records
# We will create a new Route 53 Hosted Zone for lifeontherock.org

resource "aws_route53_zone" "lifeontherock_hosted_zone" {
  name = "lifeontherock.org"

  tags = {
    Name        = "lifeontherock.org-hosted-zone"
    Project     = "LifeOnTheRockInternational"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Client      = "JohnMoreland"
  }
}

resource "aws_route53_record" "lotr_apex" {
  zone_id = aws_route53_zone.lifeontherock_hosted_zone.zone_id
  name    = "lifeontherock.org"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.lotr_cdn.domain_name
    zone_id                = aws_cloudfront_distribution.lotr_cdn.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "lotr_www" {
  zone_id = aws_route53_zone.lifeontherock_hosted_zone.zone_id
  name    = "www.lifeontherock.org"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.lotr_cdn.domain_name
    zone_id                = aws_cloudfront_distribution.lotr_cdn.hosted_zone_id
    evaluate_target_health = false
  }
}

# Output CloudFront Domain Name
output "lotr_cloudfront_domain_name" {
  description = "The domain name of the Life on the Rock CloudFront distribution."
  value       = aws_cloudfront_distribution.lotr_cdn.domain_name
}

# Output Route 53 Name Servers (CRITICAL for domain transfer)
output "lotr_nameservers" {
  description = "The Name Servers for lifeontherock.org Hosted Zone. Update your domain registrar with these!"
  value       = aws_route53_zone.lifeontherock_hosted_zone.name_servers
}
