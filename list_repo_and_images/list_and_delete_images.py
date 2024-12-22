### FILL IN LINES 96-100 BEFORE RUNNING SCRIPT

################################################################
### This script lists all ECR repositories and images in the repositories that match the given filter.
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

def initialize_ecr_client(profile_name, region_name):
    """Initialize and return an ECR client."""
    my_session = boto3.session.Session(profile_name=profile_name)
    return my_session.client('ecr', region_name=region_name)


def analyze_ecr_images(ecr_client, repository_name_filter, excluded_patterns):
    try:
        # List all repositories
        repositories = ecr_client.describe_repositories()

        # Filter repositories by name
        matching_repositories = [
            repo['repositoryName']
            for repo in repositories.get('repositories', [])
            if repository_name_filter in repo['repositoryName']
        ]

        if not matching_repositories:
            print(f"No repositories found containing '{repository_name_filter}' in their names.")
            return []

        print(f"Found repositories containing '{repository_name_filter}': {matching_repositories}")

        # Collect images to delete
        images_to_delete = []
        for repository_name in matching_repositories:
            print(f"\nAnalyzing repository: {repository_name}")

            paginator = ecr_client.get_paginator('describe_images')
            for page in paginator.paginate(repositoryName=repository_name):
                for image_detail in page.get('imageDetails', []):
                    image_tags = image_detail.get('imageTags', [])
                    image_size_in_bytes = image_detail.get('imageSizeInBytes', 0)

                    # Check if none of the tags match the excluded patterns
                    if all(
                            not fnmatch.fnmatch(tag, pattern)
                            for tag in image_tags
                            for pattern in excluded_patterns
                    ):
                        images_to_delete.append({
                            "repository": repository_name,
                            "digest": image_detail["imageDigest"],
                            "tags": image_tags,
                            "size_in_gb": image_size_in_bytes / (1024 ** 3)
                        })

        return images_to_delete

    except Exception as e:
        print(f"Error during ECR analysis: {str(e)}")
        return []


def delete_images(ecr_client, images_to_delete):
    try:
        for repository_name, images in images_to_delete.items():
            print(f"\nDeleting {len(images)} images from repository '{repository_name}'...")

            # Batch images in groups of 100
            for i in range(0, len(images), 100):
                batch = images[i:i + 100]
                delete_response = ecr_client.batch_delete_image(
                    repositoryName=repository_name,
                    imageIds=[{"imageDigest": image['digest']} for image in batch]
                )
                print(f"Deleted {len(delete_response.get('imageIds', []))} images from '{repository_name}'.")
                if delete_response.get('failures'):
                    print(f"Failures: {delete_response['failures']}")
    except Exception as e:
        print(f"Error during deletion: {str(e)}")


if __name__ == "__main__":
    # Local test parameters
    profile_name = "PROFILE_NAME"  # AWS CLI profile name, it points the running script to a specific AWS account
    region_name = "AWS_REGION" #AWS region name, e.g. us-east-1, eu-west-1, etc.
    repository_name_filter = ""  # Filter for repositories containing this word. Put "*" to list all repositories.
    excluded_patterns = []  # Tags to exclude. Empty list means no tags are excluded.

    # Initialize the ECR client
    ecr_client = initialize_ecr_client(profile_name, region_name)

    # Analyze and collect images

    if images_to_delete:
        # Calculate total size and count
        total_size = sum(image['size_in_gb'] for image in images_to_delete)
        total_count = len(images_to_delete)

        # List the images to delete
        print("\nImages to delete:")
        for image in images_to_delete:
            print(f"Repository: {image['repository']}, Digest: {image['digest']}, Tags: {image['tags']}, "
                  f"Size: {image['size_in_gb']:.2f} GB")

        # Display summary
        print(f"\nSummary: Totally {total_count} images to delete, total size is {total_size:.2f} GB.")

        # Confirm deletion
        user_input = input("\nDo you want to delete the above images? (yes/no): ").strip().lower()
        if user_input in ['yes', 'y']:
            # Group images by repository for batch deletion
            grouped_images = {}
            for image in images_to_delete:
                grouped_images.setdefault(image['repository'], []).append(image)
            delete_images(ecr_client, grouped_images)
        else:
            print("Deletion aborted by the user.")
    else:
        print("\nNo images to delete.")
