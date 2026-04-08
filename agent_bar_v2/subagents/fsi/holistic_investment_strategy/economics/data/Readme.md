# Copy world_bank_data_2025.csv to the macroeconomics data bucket
# Note: This is handled automatically by Terraform if you use it.
gcloud storage cp world_bank_data_2025.csv gs://[PROJECT_ID]-abv2-macroeconomics/fsi/economics/data/world_bank_data_2025.csv

