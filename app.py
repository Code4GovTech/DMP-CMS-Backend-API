from flask import Flask, jsonify,request,url_for
from db import SupabaseInterface
from collections import defaultdict
from flasgger import Swagger
import re,os,traceback
from utils import *
from flask_cors import CORS,cross_origin
from functools import wraps
from v2_app import v2


app = Flask(__name__)
CORS(app,supports_credentials=True)


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
@require_secret_key
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



@app.route('/v1/issues', methods=['GET'])
@require_secret_key
def v1get_issues():
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
        dmp_issue =SupabaseInterface().get_instance().client.table('dmp_issues').select('*').execute().data
        
        updated_issues = []

        for i in dmp_issue:
          val = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('dmp_issue_url',i['repo_url']).execute().data 
          if val!=[]:
            i['issues'] = val[0] #append first obj ie all are reder same issue
            i['org_id'] = val[0]['org_id']
            i['org_name'] = val[0]['org_name'] 
            
            updated_issues.append(i)
          
        # Create a defaultdict of lists
        grouped_data = defaultdict(list)
        # Group data by 'org_name'
        for item in updated_issues:
            grouped_data[item['org_name']].append(item)

        response = []
        for org_name, items in grouped_data.items():
            issues = [
                {
                    "html_url": item['issues']['html_issue_url'],
                    "id": item['issues']['comment_id'],
                    "issue_number": item['issues']['issue_number'],
                    "name": item['issues']['title']
                }
                for item in items
            ]
            
            response.append({
                "issues": issues,
                "org_id": items[0]['org_id'],
                "org_name": org_name
            })
        
        return jsonify(response)
      
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
        return jsonify({"name": data['org_name'], "description": data['org_description']})
      
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
    SUPABASE_DB = SupabaseInterface().get_instance()
    response = SUPABASE_DB.client.table('dmp_issue_updates').select('*').eq('owner', owner).eq('issue_number', issue).execute()
    if not response.data:
        return jsonify({'error': "No data found"}), 500
    data = response.data
    
    final_data = []
    w_learn_url,w_goal_url,avg,cont_details = None,None,None,None
    
    for val in data:
      issue_url = "https://api.github.com/repos/{}/{}/issues/comments".format(val['owner'],val['repo'])
      # week_avg ,cont_name,cont_id,w_goal,w_learn,weekby_avgs,org_link = find_week_avg(issue_url)
      # mentors_data = find_mentors(val['issue_url']) if val['issue_url'] else {'mentors': [], 'mentor_usernames': []}
      
      if val['body_text']:
        if "Weekly Goals" in val['body_text'] and not w_goal_url:
            w_goal_url = val['body_text']
            plain_text_body = markdown2.markdown(val['body_text'])
                
            tasks = re.findall(r'\[(x| )\]', plain_text_body)
            total_tasks = len(tasks)
            completed_tasks = tasks.count('x')
            
            avg = round((completed_tasks/total_tasks)*100) if total_tasks!=0 else 0
                  
        if "Weekly Learnings" in val['body_text'] and not w_learn_url:
            w_learn_url = val['body_text']
      
      # mentors = mentors_data['mentors']
      # ment_usernames = mentors_data['mentor_usernames']
      if not cont_details:
        cont_details = SUPABASE_DB.client.table('dmp_issues').select('*').eq('repo_url',val['dmp_issue_url']).execute().data 
      
      res = {
        "name": owner,
        "description": val['description'],
        "mentor_name": val['mentor_name'],
        "mentor_id": val['mentor_id'] ,
        "contributor_name":cont_details[0]['contributor_name'] ,
        "contributor_id": cont_details[0]['contributor_id'],
        "org_name": val['owner'],
        "org_link": val['org_link'],
        "weekly_goals_html": w_goal_url,
        "weekly_learnings_html": w_learn_url,
        "overall_progress": avg,
        "issue_url":val['html_issue_url'],
        "pr_details":None
      }
      
    pr_Data = SUPABASE_DB.client.table('dmp_pr_updates').select('*').eq('repo', val['repo']).execute()
    transformed = {"pr_details": []}
    if pr_Data.data:
      for pr in pr_Data.data:
        transformed["pr_details"].append({
            "id": pr.get("pr_id", ""),
            "name": pr.get("meta_data", ""),
            "week": determine_week(pr['created_at']),
            "link": pr.get("html_url", ""),
            "status": pr.get("status", ""),
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

          

# Register the v2 Blueprint
app.register_blueprint(v2, url_prefix='/v2')

if __name__ == '__main__':
    app.run(debug=True)