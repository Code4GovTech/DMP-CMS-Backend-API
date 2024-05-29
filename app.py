from flask import Flask, jsonify,request,url_for
from db import SupabaseInterface
from collections import defaultdict
from flasgger import Swagger
import re,markdown2,requests,os

app = Flask(__name__)

Swagger(app)


GITHUB_TOKEN =os.getenv('GITHUB_TOKEN')

headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }



# Define a list of routes that should be protected
protected_routes = ['/greeting', '/get-data', '/issues', '/issues/<owner>', '/issues/<owner>/<issue>']
SECRET_KEY =os.getenv('SECRET_KEY')

protected_routes = [
    re.compile(r'^/greeting$'),
    re.compile(r'^/get-data$'),
    re.compile(r'^/issues$'),
    re.compile(r'^/issues/[^/]+$'),  # Matches '/issues/<owner>'
    re.compile(r'^/issues/[^/]+/[^/]+$')  # Matches '/issues/<owner>/<issue>'
]


@app.route('/greeting', methods=['GET'])
def greeting():    
    """
    A simple greeting endpoint.
    ---
    responses:
      200:
        description: A greeting message
        schema:
          type: object
          properties:
            message:
              type: string
              example: Hello, welcome to my API!
    """
    response = {
        'message': 'Hello, welcome to my API!'
    }
    return jsonify(response)

@app.route('/get-data', methods=['GET'])
def get_data():
    """
    Fetch data from Supabase.
    ---
    responses:
      200:
        description: Data fetched successfully
        schema:
          type: array
          items:
            type: object
      500:
        description: Error fetching data
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_pr_updates').select('*').execute()
        data = response.data
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def group_by_owner(data):
    grouped_data = defaultdict(list)
    for record in data:
      owner = record['owner']
      grouped_data[owner].append(record)
        
        
    #Arrange data as reponse format
    res = []
    for val in grouped_data:
      dict_ = {}
      dict_['org_name'] = val
      dict_['issues'] = grouped_data[val]
      
      res.append(dict_)
      
    return {"issues":res}

@app.route('/issues', methods=['GET'])
def get_issues():
    """
    Fetch all issues and group by owner.
    ---
    responses:
      200:
        description: Issues grouped by owner
        schema:
          type: object
          additionalProperties:
            type: array
            items:
              type: object
      500:
        description: Error fetching issues
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').execute()
        data = response.data
        grouped_data = group_by_owner(data)
        return jsonify(grouped_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/issues/<owner>', methods=['GET'])
def get_issues_by_owner(owner):
    """
    Fetch issues by owner.
    ---
    parameters:
      - name: owner
        in: path
        type: string
        required: true
        description: The owner of the issues
    responses:
      200:
        description: Issues fetched successfully
        schema:
          type: array
          items:
            type: object
      500:
        description: Error fetching issues
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('owner', owner).execute()
        if not response.data:
            return jsonify({'error': "No data found"}), 500
        data = response.data
        filtered_data = [{key: item[key] for key in ['owner','body_text']} for item in data]
        data = [{**{"name": item.pop("owner"),"description": item.pop("body_text")}, **item} for item in filtered_data]
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
      

  
def find_week_avg(url):
  # url = "https://api.github.com/repos/VedantKhairnar/dmp-backend-test-repo/issues/comments"

  response = requests.get(url,headers=headers)

  if response.status_code == 200:
    issue_details = response.json()
    plain_text_body = markdown2.markdown(issue_details[0]['body'])
            
    tasks = re.findall(r'\[(x| )\]', plain_text_body)
    total_tasks = len(tasks)
    completed_tasks = tasks.count('x')
    
    avg = round((completed_tasks/total_tasks)*100) if total_tasks!=0 else 0
    
    #find weekly goal html urls
    w_goal_url = None
    w_learn_url = None
    
    for item in issue_details:
      if "Weekly Goals" in item['body']:
        w_goal_url = item['html_url']
      if "Weekly Learnings" in item['body']:
        w_learn_url = item['html_url']
    
    return avg,issue_details[0]['user']['login'],issue_details[0]['user']['id'],w_goal_url,w_learn_url
      

@app.route('/mentors', methods=['GET'])
def find_mentors(url):
    response = requests.get(url,headers=headers)

    if response.status_code == 200:
        issue_details = response.json()

        issue_body = issue_details['body']
        pattern = r"## Mentors\s*([\s\S]+?)\s*##"
        match = re.search(pattern, issue_body)

        if match:
            mentors_text = match.group(1).strip()
            # Extract individual mentor usernames
            mentors = [mentor.strip() for mentor in mentors_text.split(',')]
        else:
            mentors = []
        api_base_url = "https://api.github.com/users/"

        ment_username = []
        for val in mentors:            
          url = f"{api_base_url}{val[1:]}"
          username = requests.get(url)
          ment_username.append(username.json()['login'])
          
        return mentors,ment_username
    else:
      return [],[]

def get_pr_details(url):
  try:
    issue_url = url
    url_parts = issue_url.split("/")
    owner = url_parts[4]
    repo = url_parts[5]
    issue_number = url_parts[7]

    # GitHub API endpoint to get pull requests for the repository
    pulls_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    # Send GET request to GitHub API with authentication
    response = requests.get(pulls_url, headers=headers)
    if response.status_code == 200:
        pulls = response.json()
        return pulls      
    else:
      return []
        
        
  except Exception as e:
    raise Exception
  

@app.route('/issues/<owner>/<issue>', methods=['GET'])
def get_issues_by_owner_id(owner, issue):
  """
    Fetch issues by owner and issue number.
    ---
    parameters:
      - name: owner
        in: path
        type: string
        required: true
        description: The owner of the issues
      - name: issue
        in: path
        type: string
        required: true
        description: The issue number
        
    responses:
      200:
        description: Issues fetched successfully
        schema:
          type: array
          items:
            type: object
      500:
        description: Error fetching issues
        schema:
          type: object
          properties:
            error:
              type: string
                
  """
  try:         
    response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('owner', owner).eq('issue_number', issue).execute()
    if not response.data:
        return jsonify({'error': "No data found"}), 500
    data = response.data
    
    final_data = []
    
    for val in data:
      issue_url = "https://api.github.com/repos/{}/{}/issues/comments".format(val['owner'],val['repo'])
      week_avg ,cont_name,cont_id,w_goal,w_learn = find_week_avg(issue_url)
      
      mentors,ment_usernames = find_mentors(val['issue_url']) if val['issue_url'] else [],[]
      res = {
        "name": owner,
        "description": None,
        "mentor_name": ment_usernames,
        "mentor_id": mentors,
        "contributor_name":cont_name ,
        "contributor_id": cont_id,
        "org_name": val['owner'],
        "org_link": val['repo'],
        "weekly_goals_html": w_goal,
        "weekly_learnings_html": w_learn,
        "overall_progress": week_avg,
        "issue_url":val['issue_url'],
        "pr_details":get_pr_details(val['issue_url'])
      }
      
      # final_data.append(res)
    
      return jsonify(res),200
  except Exception as e:
    return jsonify({'error': str(e)}), 500



# Before request handler to check for the presence of the secret key
@app.before_request
def check_secret_key():
  for route_pattern in protected_routes:
    if route_pattern.match(request.path):
      secret_key = request.headers.get('X-Secret-Key')
      if secret_key != SECRET_KEY:
        return jsonify({'message': 'Unauthorized access'}), 401
      break  # Stop checking if the current route matches
          
          
if __name__ == '__main__':
    app.run(debug=True)