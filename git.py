import requests
import pandas as pd
import plotly.express as px
import datetime
from tqdm import tqdm

# Replace with your GitHub token and organization
GITHUB_TOKEN = 'github_pat'
ORG_NAME = ''

# Fetch all repositories in the organization
def fetch_repos(org_name):
    url = f'https://api.github.com/orgs/{org_name}/repos'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch repos: {response.status_code}")
        print(response.json())
        return []
    return response.json()

# Fetch commits for a repository
def fetch_commits(repo_name):
    commits = []
    url = f'https://api.github.com/repos/{ORG_NAME}/{repo_name}/commits'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    params = {'per_page': 100, 'page': 1}
    
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch commits for {repo_name}: {response.status_code}")
            print(response.json())
            break
        batch = response.json()
        if not batch:
            break
        commits.extend(batch)
        params['page'] += 1
    
    return commits

# Collect commit data from all repositories
repos = fetch_repos(ORG_NAME)
if not repos:
    print("No repositories found.")
    exit()

all_commits = []

# Use tqdm for progress bar
for repo in tqdm(repos, desc="Fetching commits", unit="repo"):
    repo_commits = fetch_commits(repo['name'])
    for commit in repo_commits:
        commit_date = commit['commit']['author']['date']
        commit_date = datetime.datetime.strptime(commit_date, '%Y-%m-%dT%H:%M:%SZ').date()
        all_commits.append({'repo': repo['name'], 'date': commit_date})

if not all_commits:
    print("No commits found.")
    exit()

# Create a DataFrame
commit_data = pd.DataFrame(all_commits)

# Group by date and count commits
commit_counts = commit_data.groupby(commit_data['date']).size().reset_index(name='commits')

# Create the 3D plot
commit_counts['date_ordinal'] = commit_counts['date'].apply(lambda x: x.toordinal())

fig = px.bar_3d(
    commit_counts, 
    x='date_ordinal', 
    y='commits', 
    z='commits', 
    color='commits', 
    labels={'date_ordinal': 'Date', 'commits': 'Number of Commits'},
    title='Git Commit History'
)

# Customize ticks for the date axis
fig.update_layout(
    scene = dict(
        xaxis = dict(
            tickmode = 'array',
            tickvals = commit_counts['date_ordinal'],
            ticktext = commit_counts['date'].astype(str)
        )
    )
)

fig.show()
