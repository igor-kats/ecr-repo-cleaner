### FILL IN LINES 184-187 BEFORE RUNNING SCRIPT


################################################################
### This script lists all ECR repositories and images in the repositories that match the given filter.
### This script is the refactored version of the script `list_and_delete_images.py`.
### The script uses classes and data classes to organize the code and data.
### The script provides more structured and reusable components for interacting with AWS ECR.
### The script separates the ECR operations into a class for better organization and readability.

### It then prompts the user to confirm the deletion of the images.
### The script uses pagination to handle large numbers of repositories and images.
### The script also allows for excluding images based on tag patterns.
### The script uses a paginator to retrieve images in batches of 100 for deletion.
### The script is designed to be run from the command line and requires user input to confirm deletion.
### The script can be customized by setting the profile name, region name, repository name filter, and excluded patterns.
### The script can be used to analyze and delete ECR images based on specific criteria.
### The script provides a summary of the images to be deleted before proceeding with the deletion process.
### The script uses the `boto3` library to interact with AWS services.
### The script is designed to be run in a Python environment with the `boto3` library installed.
### The script can be run by executing `python list_and_delete_images.py` in a terminal or command prompt.
################################################################


import boto3
import fnmatch
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ECRImage:
    """Data class to represent an ECR image."""
    repository: str
    digest: str
    tags: List[str]
    size_in_gb: float


class ECRManager:
    """Class to manage AWS ECR operations."""

    def __init__(self, profile_name: str, region_name: str):
        """Initialize ECR manager with AWS credentials."""
        self.ecr_client = self._initialize_ecr_client(profile_name, region_name)

    @staticmethod
    def _initialize_ecr_client(profile_name: str, region_name: str) -> boto3.client:
        """Initialize and return an ECR client."""
        try:
            session = boto3.session.Session(profile_name=profile_name)
            return session.client('ecr', region_name=region_name)
        except Exception as e:
            logger.error(f"Failed to initialize ECR client: {e}")
            raise

    def get_matching_repositories(self, repository_name_filter: str) -> List[str]:
        """Get repositories matching the filter."""
        try:
            repositories = self.ecr_client.describe_repositories()
            matching_repos = [
                repo['repositoryName']
                for repo in repositories.get('repositories', [])
                if repository_name_filter in repo['repositoryName']
            ]

            if not matching_repos:
                logger.info(f"No repositories found containing '{repository_name_filter}'")
            else:
                logger.info(f"Found repositories: {matching_repos}")

            return matching_repos

        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            return []

    def analyze_images(
            self,
            repository_name_filter: str,
            excluded_patterns: List[str]
    ) -> List[ECRImage]:
        """Analyze ECR images and return those eligible for deletion."""
        try:
            matching_repositories = self.get_matching_repositories(repository_name_filter)
            images_to_delete = []

            for repository_name in matching_repositories:
                logger.info(f"Analyzing repository: {repository_name}")
                images_to_delete.extend(
                    self._get_deletable_images(repository_name, excluded_patterns)
                )

            return images_to_delete

        except Exception as e:
            logger.error(f"Error during ECR analysis: {e}")
            return []

    def _get_deletable_images(
            self,
            repository_name: str,
            excluded_patterns: List[str]
    ) -> List[ECRImage]:
        """Get list of images that can be deleted from a repository."""
        deletable_images = []
        paginator = self.ecr_client.get_paginator('describe_images')

        try:
            for page in paginator.paginate(repositoryName=repository_name):
                for image_detail in page.get('imageDetails', []):
                    image_tags = image_detail.get('imageTags', [])

                    if self._should_delete_image(image_tags, excluded_patterns):
                        deletable_images.append(ECRImage(
                            repository=repository_name,
                            digest=image_detail["imageDigest"],
                            tags=image_tags,
                            size_in_gb=image_detail.get('imageSizeInBytes', 0) / (1024 ** 3)
                        ))

            return deletable_images

        except Exception as e:
            logger.error(f"Error getting images from repository {repository_name}: {e}")
            return []

    @staticmethod
    def _should_delete_image(tags: List[str], excluded_patterns: List[str]) -> bool:
        """Determine if an image should be deleted based on its tags."""
        return all(
            not fnmatch.fnmatch(tag, pattern)
            for tag in tags
            for pattern in excluded_patterns
        )

    def delete_images(self, images_to_delete: List[ECRImage]) -> None:
        """Delete images in batches of 100."""
        grouped_images = defaultdict(list)
        for image in images_to_delete:
            grouped_images[image.repository].append(image)

        for repository_name, images in grouped_images.items():
            logger.info(f"Deleting {len(images)} images from '{repository_name}'...")

            for batch in self._batch_images(images):
                try:
                    response = self.ecr_client.batch_delete_image(
                        repositoryName=repository_name,
                        imageIds=[{"imageDigest": image.digest} for image in batch]
                    )

                    self._log_deletion_results(repository_name, response)

                except Exception as e:
                    logger.error(f"Error deleting batch from {repository_name}: {e}")

    @staticmethod
    def _batch_images(images: List[ECRImage], batch_size: int = 100) -> List[List[ECRImage]]:
        """Split images into batches."""
        return [images[i:i + batch_size] for i in range(0, len(images), batch_size)]

    @staticmethod
    def _log_deletion_results(repository_name: str, response: Dict[str, Any]) -> None:
        """Log the results of a batch deletion."""
        deleted = len(response.get('imageIds', []))
        failures = response.get('failures', [])

        logger.info(f"Deleted {deleted} images from '{repository_name}'")
        if failures:
            logger.warning(f"Failures: {failures}")


def main():
    """Main execution function."""
    # Configuration
    CONFIG = {
        'profile_name': "PROFILE_NAME",
        'region_name': "REGION_NAME",
        'repository_filter': "",
        'excluded_patterns': []
    }

    try:
        # Initialize ECR manager
        ecr_manager = ECRManager(CONFIG['profile_name'], CONFIG['region_name'])

        # Analyze images
        images_to_delete = ecr_manager.analyze_images(
            CONFIG['repository_filter'],
            CONFIG['excluded_patterns']
        )

        if not images_to_delete:
            logger.info("No images to delete.")
            return

        # Display results
        total_size = sum(image.size_in_gb for image in images_to_delete)
        logger.info("\nImages to delete:")
        for image in images_to_delete:
            logger.info(
                f"Repository: {image.repository}, "
                f"Tags: {image.tags}, "
                f"Size: {image.size_in_gb:.2f} GB"
            )
        logger.info(f"\nSummary: {len(images_to_delete)} images to delete, "
                    f"total size: {total_size:.2f} GB")

        # Confirm deletion
        if input("\nDelete these images? (yes/no): ").lower().strip() in ['yes', 'y']:
            ecr_manager.delete_images(images_to_delete)
        else:
            logger.info("Deletion aborted by user.")

    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        raise


if __name__ == "__main__":
    main()