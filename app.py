from flask import Flask, jsonify,request,url_for
from db import SupabaseInterface
from collections import defaultdict
from flasgger import Swagger
import re,os,traceback
from utils import *
from flask_cors import CORS,cross_origin
from functools import wraps


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)


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
@cross_origin(supports_credentials=True) # added this to my endpoint 
def greeting():    
    response = {
        'message': 'Hello, welcome to my API!'
    }
    return jsonify(response)
  
  

# Custom decorator to validate secret key
def require_secret_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret_key = request.headers.get('X-Secret-Key')
        if secret_key != SECRET_KEY:
            return jsonify({'message': 'Unauthorized access'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/get-data', methods=['GET'])
@cross_origin(supports_credentials=True)
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


@app.route('/issues', methods=['GET'])
@cross_origin(supports_credentials=True)
@require_secret_key
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
                
        #group data based on issues
        grouped_data = defaultdict(list)
        for record in data:
            issue_url = record['issue_url']
            grouped_data[issue_url].append({
                'id': record['id'],
                'name': record['body_text']
            })

        result = [{'issue_url': issue_url, 'issues': issues} for issue_url, issues in grouped_data.items()]
        
        grouped_data = group_by_owner(result)
        return jsonify(grouped_data)
      
    except Exception as e:
        error_traceback = traceback.format_exc()
        return jsonify({'error': str(e), 'traceback': error_traceback}), 500
      
@app.route('/issues/<owner>', methods=['GET'])
@cross_origin(supports_credentials=True)
@require_secret_key
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
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('owner', owner).order('comment_updated_at', desc=True).execute()
        if not response.data:
            return jsonify({'error': "No data found"}), 500
        data = response.data[0]
        repo_details = get_repo_details(data['owner'],data['repo'])
        org_name = repo_details['ower']['login'] if repo_details['owner']['login'] else None
        org_desc = repo_details['description']  if repo_details['description']  else None
        return jsonify({"name": org_name, "description": org_desc})
      
    except Exception as e:
        error_traceback = traceback.format_exc()
        return jsonify({'error': str(e), 'traceback': error_traceback}), 500
      

  
@app.route('/issues/<owner>/<issue>', methods=['GET'])
@cross_origin(supports_credentials=True)
@require_secret_key
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
      week_avg ,cont_name,cont_id,w_goal,w_learn,weekby_avgs,org_link = find_week_avg(issue_url)
      mentors_data = find_mentors(val['issue_url']) if val['issue_url'] else {'mentors': [], 'mentor_usernames': []}
      
      mentors = mentors_data['mentors']
      ment_usernames = mentors_data['mentor_usernames']
      
      res = {
        "name": owner,
        "description": mentors_data['desc'],
        "mentor_name": ment_usernames,
        "mentor_id": mentors,
        "contributor_name":cont_name ,
        "contributor_id": cont_id,
        "org_name": val['owner'],
        "org_link": org_link,
        "weekly_goals_html": w_goal,
        "weekly_learnings_html": w_learn,
        "overall_progress": week_avg,
        "issue_url":val['html_url'],
        "pr_details":get_pr_details(val['issue_url'])
      }
     
      transformed = {"pr_details": []}
      
      for pr in res.get("pr_details", []):
        transformed["pr_details"].append({
            "id": pr.get("id", ""),
            "name": pr.get("title", ""),
            "week": determine_week(pr['created_at']),
            "link": pr.get("html_url", ""),
            "status": pr.get("state", ""),
        })
                
      res['pr_details'] = transformed['pr_details']
      
      # Adding each week as a separate key
      # for week in weekby_avgs:
      #   res.update(week)
        
      # final_data.append(res)
    
      return jsonify(res),200
  except Exception as e:
      error_traceback = traceback.format_exc()
      return jsonify({'error': str(e), 'traceback': error_traceback}), 500



# Before request handler to check for the presence of the secret key
# @app.before_request
def check_secret_key():
  for route_pattern in protected_routes:
    if route_pattern.match(request.path):
      secret_key = request.headers.get('X-Secret-Key')
      if secret_key != SECRET_KEY:
        return jsonify({'message': 'Unauthorized access'}), 401
      break  # Stop checking if the current route matches

          
if __name__ == '__main__':
    app.run(debug=True)