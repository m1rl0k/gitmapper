import requests
import pandas as pd
import plotly.graph_objects as go
import datetime
import numpy as np

# Replace with your GitHub token and organization
GITHUB_TOKEN = 'your_github_token'
ORG_NAME = 'your_org_name'

# Fetch all repositories in the organization
def fetch_repos(org_name):
    url = f'https://api.github.com/orgs/{org_name}/repos'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
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
            break
        batch = response.json()
        if not batch:
            break
        commits.extend(batch)
        params['page'] += 1
    
    return commits

# Collect commit data from all repositories
repos = fetch_repos(ORG_NAME)
all_commits = []

for repo in repos:
    repo_commits = fetch_commits(repo['name'])
    for commit in repo_commits:
        commit_date = commit['commit']['author']['date']
        commit_date = datetime.datetime.strptime(commit_date, '%Y-%m-%dT%H:%M:%SZ').date()
        all_commits.append({'repo': repo['name'], 'date': commit_date})

# Create a DataFrame
commit_data = pd.DataFrame(all_commits)

# Group by date and count commits
commit_counts = commit_data.groupby(commit_data['date']).size().reset_index(name='commits')

# Create the 3D plot
fig = go.Figure()

# Dates to ordinal
commit_counts['date_ordinal'] = commit_counts['date'].apply(lambda x: x.toordinal())

# Add bars
fig.add_trace(go.Bar3d(
    x=commit_counts['date_ordinal'],  # Dates
    y=[0] * len(commit_counts),       # Y-axis placeholder
    z=[0] * len(commit_counts),       # Z start (base of bars)
    dx=1,                             # Width of bars
    dy=1,                             # Depth of bars
    dz=commit_counts['commits'],      # Height of bars
    text=commit_counts['date'],       # Hover text
    hoverinfo='text+z',
    marker=dict(
        color=commit_counts['commits'],  # Color by number of commits
        colorscale='Viridis',            # Color scale
        opacity=0.9,
        line=dict(width=1, color='DarkSlateGrey')
    )
))

# Customize layout
fig.update_layout(
    title='Git Commit History',
    scene=dict(
        xaxis_title='Date',
        yaxis_title='',
        zaxis_title='Number of Commits',
        xaxis=dict(
            tickvals=np.arange(commit_counts['date_ordinal'].min(), commit_counts['date_ordinal'].max(), step=30),
            ticktext=pd.to_datetime(np.arange(commit_counts['date_ordinal'].min(), commit_counts['date_ordinal'].max(), step=30), unit='D').strftime('%Y-%m-%d')
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
frames = [go.Frame(data=[go.Bar3d(
    x=commit_counts['date_ordinal'][:k+1],
    y=[0] * (k+1),
    z=[0] * (k+1),
    dx=1,
    dy=1,
    dz=commit_counts['commits'][:k+1],
    marker=dict(color=commit_counts['commits'][:k+1], colorscale='Viridis')
)]) for k in range(len(commit_counts))]

fig.frames = frames

fig.show()
