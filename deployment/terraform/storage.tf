# 1. Default Data Bucket
resource "google_storage_bucket" "default_data_bucket" {
  name          = "${var.project_id}-abv2-agents-default-data"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 2. Sub-agent requirements (cross_industry/product_ad_generation)
resource "google_storage_bucket" "product_ad_generation_bucket" {
  name          = "${var.project_id}-abv2-cross-product-ad-generation"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 3. Campaign Manager Sub-agent
resource "google_storage_bucket" "campaign_manager_bucket" {
  name          = "${var.project_id}-abv2-global-campaign-manager-agent"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 4. Meeting Intelligence Sub-agent
resource "google_storage_bucket" "meeting_intelligence_bucket" {
  name          = "${var.project_id}-abv2-meeting-intelligence"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}
