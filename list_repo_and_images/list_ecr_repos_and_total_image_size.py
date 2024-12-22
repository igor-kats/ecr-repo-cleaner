### FILL IN LINES 65-66 BEFORE RUNNING SCRIPT

################################################################
### This script retrieves all ECR repositories
### and calculates the total size of images in each repository,
### returning a list which looks like "repo name + total image size in GB".
### THIS SCRIPT DOES NOT DELETE ANY IMAGES.

### The script can be run by executing `python list_ecr_repos_and_total_image_size.py` in a terminal or command prompt.
################################################################

import boto3

# Initialize and return an ECR client using the specified AWS profile and region.
def initialize_ecr_client(profile_name, region_name):
    # Create a session using the provided AWS CLI profile
    session = boto3.session.Session(profile_name=profile_name)
    # Return an ECR client object for the specified region
    return session.client('ecr', region_name=region_name)

# Retrieve all ECR repositories and calculate the total size of images in each repository.
def get_repositories_with_sizes(ecr_client):
    try:
        # Use a paginator to handle cases where there are many repositories
        paginator = ecr_client.get_paginator('describe_repositories')
        repositories = []
        for page in paginator.paginate():
            # Append repositories from each page of results
            repositories.extend(page.get('repositories', []))

        # If no repositories are found, notify the user and return an empty dictionary
        if not repositories:
            print("No repositories found.")
            return {}

        print(f"Found {len(repositories)} repositories.")

        # Dictionary to store repository names and their corresponding total sizes (in GB)
        repository_sizes = {}
        for repo in repositories:
            repository_name = repo['repositoryName']  # Extract the repository name
            print(f"Analyzing repository: {repository_name}")

            total_size = 0  # Initialize the total size for the current repository
            # Use a paginator to handle cases where there are many images in a repository
            paginator = ecr_client.get_paginator('describe_images')
            for page in paginator.paginate(repositoryName=repository_name):
                for image_detail in page.get('imageDetails', []):
                    # Accumulate the size of each image in bytes
                    total_size += image_detail.get('imageSizeInBytes', 0)

            # Convert the total size from bytes to gigabytes and store it in the dictionary
            repository_sizes[repository_name] = total_size / (1024 ** 3)

        # Sort the repositories by size in descending order for easier analysis
        sorted_repository_sizes = dict(sorted(repository_sizes.items(), key=lambda item: item[1], reverse=True))

        return sorted_repository_sizes  # Return the sorted dictionary of repository sizes

    except Exception as e:
        # Handle and display any errors that occur during the process
        print(f"Error during repository analysis: {str(e)}")
        return {}

if __name__ == "__main__":
    # AWS CLI profile and region to be used for the ECR client
    profile_name = "PROFILE_NAME" #fill here you AWS mfa profile name
    region_name = "eu-west-1" #fill here the region name, eu-west-1 is mentioned as an example

    # Initialize the ECR client using the specified profile and region
    ecr_client = initialize_ecr_client(profile_name, region_name)

    # Retrieve repository sizes and display the results
    repository_sizes = get_repositories_with_sizes(ecr_client)

    if repository_sizes:
        # Print each repository and its total size in descending order of size
        print("\nRepository sizes (sorted by size, descending):")
        for repository_name, size_in_gb in repository_sizes.items():
            print(f"Repository: {repository_name}, Total Size: {size_in_gb:.2f} GB")
    else:
        # Notify the user if no repository data is available
        print("\nNo repository data available.")
