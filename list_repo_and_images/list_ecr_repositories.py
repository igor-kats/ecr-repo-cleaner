### FILL IN LINES 10-11 BEFORE RUNNING SCRIPT

################################################################
### The simplest script returning a list of ECR repositories.
### The script can be run by executing `python list_ecr_repositories.py` in a terminal or command prompt.
################################################################

import boto3

def test_list_repositories():
    
    my_session = boto3.session.Session(profile_name="") #fill here you AWS mfa profile name
    ecr_client = my_session.client('ecr', region_name='eu-west-1') #fill here the region name, eu-west-1 is mentioned as an example
    try:
        response = ecr_client.describe_repositories()
        print("Repositories:", response['repositories'])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_list_repositories()
