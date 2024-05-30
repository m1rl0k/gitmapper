import requests
import pandas as pd
import plotly.graph_objects as go
import datetime
from tqdm import tqdm

# Replace with your GitHub token, organization, and username
GITHUB_TOKEN = 'your_github_token'
ORG_NAME = 'your_org_name'
USERNAME = 'your_github_username'

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

# Fetch commits for a repository by the specific user
def fetch_commits(repo_name):
    commits = []
    url = f'https://api.github.com/repos/{ORG_NAME}/{repo_name}/commits'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    params = {'author': USERNAME, 'per_page': 100, 'page': 1}
    
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            if response.status_code == 409:  # Repository is empty
                print(f"Repository {repo_name} is empty.")
            else:
                print(f"Failed to fetch commits for {repo_name}: {response.status_code}")
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
    try:
        repo_commits = fetch_commits(repo['name'])
        for commit in repo_commits:
            commit_date = commit['commit']['author']['date']
            commit_date = datetime.datetime.strptime(commit_date, '%Y-%m-%dT%H:%M:%SZ').date()
            all_commits.append({'repo': repo['name'], 'date': commit_date})
    except Exception as e:
        print(f"Error fetching commits for {repo['name']}: {e}")

if not all_commits:
    print("No commits found.")
    exit()

# Create a DataFrame
commit_data = pd.DataFrame(all_commits)

# Group by date and count commits
commit_counts = commit_data.groupby(commit_data['date']).size().reset_index(name='commits')

# Create the 3D plot using plotly.graph_objects
commit_counts['date_ordinal'] = commit_counts['date'].apply(lambda x: x.toordinal())

fig = go.Figure(data=[
    go.Scatter3d(
        x=commit_counts['date_ordinal'],
        y=[0] * len(commit_counts),
        z=commit_counts['commits'],
        mode='markers',
        marker=dict(
            size=commit_counts['commits'],
            color=commit_counts['commits'],
            colorscale='Viridis',
            opacity=0.8
        ),
        hovertext=commit_counts['date'],
        hoverinfo='text+z'
    )
])

# Customize layout
fig.update_layout(
    title='Git Commit History',
    scene=dict(
        xaxis_title='Date',
        yaxis_title='Commits',
        zaxis_title='Number of Commits',
        xaxis=dict(
            tickmode='array',
            tickvals=commit_counts['date_ordinal'],
            ticktext=commit_counts['date'].astype(str)
        ),
        camera_eye=dict(x=1.5, y=1.5, z=1.5)
    ),
    updatemenus=[{
        'buttons': [
            {
                'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True, 'transition': {'duration': 300}}],
                'label': 'Play',
                'method': 'animate'
            },
            {
                'args': [[None], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}],
                'label': 'Pause',
                'method': 'animate'
            }
        ],
        'direction': 'left',
        'pad': {'r': 10, 't': 87},
        'showactive': False,
        'type': 'buttons',
        'x': 0.1,
        'xanchor': 'right',
        'y': 0,
        'yanchor': 'top'
    }],
)

# Animation frames
frames = [go.Frame(data=[go.Scatter3d(
    x=commit_counts['date_ordinal'][:k+1],
    y=[0] * (k+1),
    z=commit_counts['commits'][:k+1],
    marker=dict(size=commit_counts['commits'][:k+1], color=commit_counts['commits'][:k+1], colorscale='Viridis')
)]) for k in range(len(commit_counts))]

fig.frames = frames

fig.show()
