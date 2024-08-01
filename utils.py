import requests,re,markdown2,os
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil import parser
from flask import  jsonify,request
from functools import wraps


GITHUB_TOKEN =os.getenv('GITHUB_TOKEN')
SECRET_KEY =os.getenv('SECRET_KEY')


headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }



# Custom decorator to validate secret key
def require_secret_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret_key = request.headers.get('X-Secret-Key')
        if secret_key != SECRET_KEY:
            return jsonify({'message': 'Unauthorized access'}), 401
        return f(*args, **kwargs)
    return decorated_function


def find_org_data(url):
  try:
    url_parts = url.split("/")
    owner = url_parts[4]
    repo = url_parts[5]
    
    # Fetch repository details to get organization info
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_response = requests.get(repo_url, headers=headers)
    repo_data = repo_response.json()
    if repo_data:
        org_name = repo_data['owner']['login']
        org_id = repo_data['owner']['id']
    else:
        org_name = None
        org_id = None
    return {"org_id":org_id,"org_name":org_name}
            
  except Exception as e:
    return {"org_id":None,"org_name":None}




def get_issue_details(issue_url):
    url_parts = issue_url.split("/")
    owner = url_parts[4]
    repo = url_parts[5]
    issue_number = url_parts[6]

    # GitHub API endpoint to get the issue details
    issue_api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    # Send GET request to GitHub API with authentication
    response = requests.get(issue_api_url, headers=headers)
    if response.status_code == 200:
        issue_data = response.json()
        return [{'id': issue['id'], 'name': issue['title'],'html_url':issue['html_url'],'issue_number':issue['number']} for issue in issue_data if "pull_request" not in issue]
    else:
        return {'id': None, 'name': None ,'html_url':None,'issue_number':None}
      
      

def group_by_owner(data):    
    res = []
    for record in data:
      org_data = find_org_data(record['issue_url'])
      dict_ = {}
      dict_['org_name'] = org_data['org_name']
      dict_['org_id'] = org_data['org_id']
      dict_['issues'] = get_issue_details(record['issue_url'])
      res.append(dict_)
      
    
    # org_dict = defaultdict(lambda: {'issues': [], 'org_id': None, 'org_name': None})
    # for entry in res:
    #     org_id = entry['org_id']
    #     org_name = entry['org_name']
        
    #     org_dict[org_id]['issues'].extend(entry['issues'])
    #     org_dict[org_id]['org_id'] = org_id
    #     org_dict[org_id]['org_name'] = org_name
    
        
    # return  list(org_dict.values())
    return res


def find_week_data(issue_details):
    try:
        #find how many weeks in reponse
        weekly_updates = []
        for item in issue_details:
            if "Weekly Goals" in item["body"]:
                week_match = re.search(r'Week \d+', item["body"])
                if week_match:
                    weekly_updates.append({
                        "id": item["id"],
                        "val":item,
                        "week": week_match.group(0)
                    })
                    
        val = []
                            
        for week in weekly_updates:
            
            plain_text_body = markdown2.markdown(week['val']['body'])
                
            tasks = re.findall(r'\[(x| )\]', plain_text_body)
            total_tasks = len(tasks)
            completed_tasks = tasks.count('x')
            
            avg = round((completed_tasks/total_tasks)*100) if total_tasks!=0 else 0
            
            # week['avg'] = avg
            # week['val'] = None
            week[str(week['week'])+' percentage'] = avg
            del week['val']
            del week['id']
            del week['week']
            val.append(week)
            
        return val
                                    
    except Exception as e:
        return {}
    
      
  
def find_week_avg(url):

  response = requests.get(url,headers=headers)
  if response.status_code == 200:
    issue_details = response.json()
    
    # week_avgs = find_week_data(issue_details) phase 2
    week_avgs = None
                              
    w_learn_url = None
    w_goal_url = None
    avg = 0
    for item in issue_details:
        
        if "Weekly Goals" in item['body']:
            w_goal_url = item['body']
            plain_text_body = markdown2.markdown(issue_details[0]['body'])
                
            tasks = re.findall(r'\[(x| )\]', plain_text_body)
            total_tasks = len(tasks)
            completed_tasks = tasks.count('x')
            
            avg = round((completed_tasks/total_tasks)*100) if total_tasks!=0 else 0
                
        if "Weekly Learnings" in item['body']:
            w_learn_url = item['body']
        
    
    return avg,issue_details[0]['user']['login'],issue_details[0]['user']['id'],w_goal_url,w_learn_url,week_avgs,issue_details[0]['user']['html_url']
      

def find_mentors(url):
    response = requests.get(url,headers=headers)

    if response.status_code == 200:
        issue_details = response.json()

        issue_body = issue_details['body']
        pattern = r"## Mentors\s*([\s\S]+?)\s*##"
        disc_pattern = r"## Desc 1\s*([\s\S]+?)\s*##"
        disc_match = re.search(disc_pattern, issue_body)
        
        disc_text = disc_match.group(1).strip() if disc_match else None
            
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
          username = requests.get(url,headers=headers)
          
          ment_username.append(username.json()['login'])
        return {
            'mentors': mentors,
            'mentor_usernames': ment_username,
            'desc':disc_text
        }
    else:
      return {
            'mentors': [],
            'mentor_usernames': [],
            'desc':None
        }

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
    
        


def get_repo_details(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    


def determine_week(input_date_str, start_date_str='2024-06-11'):
    try:
        # Convert the start date string to a datetime object
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        input_date = parser.parse(input_date_str).replace(tzinfo=None) if type(input_date_str) == str else input_date_str.replace(tzinfo=None)
        
        # Calculate the difference in days
        difference_in_days = (input_date - start_date).days        
        if difference_in_days < 0:
            return "Week 0"
        week_number = (difference_in_days // 7) + 1
        
        return f"Week {week_number}"
    
    except Exception as e:
        return "Week -1"

    
    
