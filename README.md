# ecr-repo-cleaner

## Overview
This repository contains a few Python scripts for managing and cleaning up images in AWS Elastic Container Registry (ECR). The script is designed to identify and delete images based on specific repository filters and tag exclusions.
Besides it it contains a couple of easy-to-use list repo and retrieve image size scripts.

### Key Features
- Filters ECR repositories by name.
- Excludes images based on tag patterns, which allows to use "not equal" conditions with wildcards, which is missing in AWS lifecycle policies.
- Groups images by repository for efficient batch deletion.
- Provides detailed logging for analysis and troubleshooting.
- Handles pagination for large datasets.

## Prerequisites

### AWS Setup
1. Ensure you have AWS CLI installed and configured with the necessary permissions:
    - `ecr:DescribeRepositories`
    - `ecr:DescribeImages`
    - `ecr:BatchDeleteImage`

2. Create a profile in your AWS credentials file for the desired account.

### Python Environment
1. Python 3.7+
2. Install dependencies:
   ```bash
   pip install boto3
   ```

## Usage

### Script Parameters
- **`profile_name`**: AWS CLI profile name.
- **`region_name`**: AWS region where the ECR is hosted.
- **`repository_name_filter`**: Substring to match repository names.
- **`excluded_patterns`**: List of patterns to exclude images based on their tags.

### Running the Script

1. Clone this repository:
   ```bash
   git clone https://github.com/your-repo/ecr-image-cleanup.git
   cd ecr-image-cleanup
   ```

2. Execute the script:
   ```bash
   python ecr_cleanup.py
   ```

3. Sample invocation in the script:
   ```python
   profile_name = "your-aws-profile"
   region_name = "us-east-1"   ###example region
   repository_name_filter = "your-repository-filter"
   excluded_patterns = ["*latest*", "*develop*"]

   manager = ECRManager(profile_name, region_name)
   images_to_delete = manager.analyze_images(repository_name_filter, excluded_patterns)
   manager.delete_images(images_to_delete)
   ```

## Script Breakdown

### Classes and Methods

#### `ECRImage`
A data class representing an ECR image, including:
- Repository name
- Digest
- Tags
- Size in GB

#### `ECRManager`
Manages ECR operations:
- **Initialization**: Creates a boto3 client using the provided profile and region.
- **`get_matching_repositories`**: Retrieves repositories matching the provided filter.
- **`analyze_images`**: Identifies deletable images based on tag exclusions.
- **`_get_deletable_images`**: Paginates through repository images and applies exclusion filters.
- **`delete_images`**: Deletes images in batches (up to 100 per API call).

### Logging
Logs provide detailed output at various stages:
- Found repositories
- Images analyzed and marked for deletion
- Batch deletion results, including failures

## Configuration

### Environment Variables
(Optional) Define AWS credentials and region via environment variables instead of using a profile:
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=your-region
```

### Customizing Exclusions
Modify the `excluded_patterns` list to exclude images based on tag patterns:
```python
excluded_patterns = ["*v1.*", "*test*"]
```

## Limitations
- Deletes up to 100 images per API call (AWS limit).
- Exclusions rely on tag patterns; untagged images will not match any exclusion.

## Contributions
Contributions are welcome! Open an issue or submit a pull request for improvements or bug fixes.

## License
This project is licensed under the MIT License, what means the project is open-source, allowing anyone to use, modify, and distribute the code with minimal restrictions, provided the original license and copyright notice are included.

## Disclaimer
Use this script with caution. Deleting images is irreversible. Always test in a development environment before applying to production.

