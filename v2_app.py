import traceback,re
from flask import Blueprint, jsonify, request
import markdown2
from utils import require_secret_key
from db import SupabaseInterface
from utils import determine_week
from v2_utils import calculate_overall_progress, define_link_data, week_data_formatter

v2 = Blueprint('v2', __name__)


@v2.route('/issues/<owner>/<issue>', methods=['GET'])
@require_secret_key
def get_issues_by_owner_id_v2(owner, issue):
    try:                 
        SUPABASE_DB = SupabaseInterface().get_instance()
        # Fetch issue updates based on owner and issue number
        
        url = f"https://github.com/{owner}"        
        
        # import pdb;pdb.set_trace()
        actual_owner = SUPABASE_DB.client.table('dmp_orgs').select('id','name','repo_owner').like('name',owner).execute().data
        repo_owner =actual_owner[0]['repo_owner'] if actual_owner else ""
        #create url with repo owner
        url = f"https://github.com/{repo_owner}" if repo_owner else None
        

        dmp_issue_id = SUPABASE_DB.client.table('dmp_issues').select('*').like('issue_url', f'%{url}%').eq('id', issue).execute()
        if not dmp_issue_id.data:
          return jsonify({'error': "No data found"}), 500
        
        dmp_issue_id = dmp_issue_id.data[0]        
        response = SUPABASE_DB.client.table('dmp_issue_updates').select('*').eq('dmp_id', dmp_issue_id['id']).execute()

        if not response.data:
            return jsonify({'error': "No data found"}), 500

        data = response.data
        
        final_data = []
        w_learn_url,w_goal_url,avg,cont_details,plain_text_body,plain_text_wurl = None,None,None,None,None,None

        
        for val in data:
            # issue_url = "https://api.github.com/repos/{}/{}/issues/comments".format(val['owner'],val['repo'])
            # week_avg ,cont_name,cont_id,w_goal,w_learn,weekby_avgs,org_link = find_week_avg(issue_url)
            # mentors_data = find_mentors(val['issue_url']) if val['issue_url'] else {'mentors': [], 'mentor_usernames': []}
            
            if val['body_text']:                                
                if ("Weekly Goals" in val['body_text'] and not w_goal_url) and ("@"+val['created_by'].lower() == dmp_issue_id['mentor_username'].lower() if dmp_issue_id['mentor_username'] else None):
                    w_goal_url = val['body_text']
                    plain_text_body = markdown2.markdown(val['body_text'])
                    tasks = re.findall(r'\[(x| )\]', plain_text_body)
                    total_tasks = len(tasks)
                    completed_tasks = tasks.count('x')
                    avg = round((completed_tasks/total_tasks)*100) if total_tasks!=0 else 0

                if ("Weekly Learnings" in val['body_text'] and not w_learn_url):
                    w_learn_url = val['body_text']
                    plain_text_wurl = markdown2.markdown(val['body_text'])

            
            # mentors = mentors_data['mentors']
            # ment_usernames = mentors_data['mentor_usernames']
            if not cont_details:
                cont_details = dmp_issue_id['contributor_username']
        week_data = week_data_formatter(plain_text_body,"Goals")
        res = {
            "name": dmp_issue_id['title'],
            "description": dmp_issue_id['description'],
            "mentor": define_link_data(dmp_issue_id['mentor_username']),
            "mentor_id": dmp_issue_id['mentor_username'] ,
            "contributor":define_link_data(cont_details),
            # "contributor_id": cont_details[0]['contributor_id'],
            "org": define_link_data(repo_owner)[0] if repo_owner else None,
            "weekly_goals_html": w_goal_url,
            "weekly_learnings_html": w_learn_url,
            "overall_progress":calculate_overall_progress(week_data,12),
            "issue_url":dmp_issue_id['issue_url'],
            "pr_details":None,
            "weekly_goals":week_data,
            "weekly_learnings":week_data_formatter(plain_text_wurl,"Learnings")
        }
        
        
        pr_Data = SUPABASE_DB.client.table('dmp_pr_updates').select('*').eq('dmp_id', dmp_issue_id['id']).like('title', f'%#{issue} - %').execute()
        transformed = {"pr_details": []}
        if pr_Data.data:
            for pr in pr_Data.data:
                transformed["pr_details"].append({
                    "id": pr.get("pr_id", ""),
                    "name": pr.get("title", ""),
                    "week": determine_week(pr['created_at']),
                    "link": pr.get("link", ""),
                    "status": pr.get("status", ""),
                })
                
        res['pr_details'] = transformed['pr_details']
                
        return jsonify(res),200
  
    except Exception as e:
        error_traceback = traceback.format_exc()
        return jsonify({'error': str(e), 'traceback': error_traceback}), 200
