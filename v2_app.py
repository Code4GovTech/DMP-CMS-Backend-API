import traceback,re
from flask import Blueprint, jsonify, request
import markdown2
from utils import require_secret_key
from db import SupabaseInterface
from utils import determine_week
from v2_utils import calculate_overall_progress, define_mentors_data, week_data_formatter

v2 = Blueprint('v2', __name__)


@v2.route('/issues/<owner>/<issue>', methods=['GET'])
@require_secret_key
def get_issues_by_owner_id_v2(owner, issue):
    try:         
        SUPABASE_DB = SupabaseInterface().get_instance()
        response = SUPABASE_DB.client.table('dmp_issue_updates').select('*').eq('owner', owner).eq('issue_number', issue).execute()
        if not response.data:
            return jsonify({'error': "No data found"}), 200
        data = response.data
        
        final_data = []
        w_learn_url,w_goal_url,avg,cont_details,plain_text_body,plain_text_wurl = None,None,None,None,None,None
        
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
                    plain_text_wurl = markdown2.markdown(val['body_text'])

            
            # mentors = mentors_data['mentors']
            # ment_usernames = mentors_data['mentor_usernames']
            if not cont_details:
                cont_details = SUPABASE_DB.client.table('dmp_issues').select('*').eq('repo_url',val['dmp_issue_url']).execute().data 
        
        
        week_data = week_data_formatter(plain_text_body,"Goals")
        res = {
            "name": owner,
            "description": val['description'],
            "mentor": define_mentors_data(val['mentor_name']),
            "mentor_id": val['mentor_id'] ,
            "contributor":define_mentors_data(cont_details[0]['contributor_name']),
            # "contributor_id": cont_details[0]['contributor_id'],
            "org": define_mentors_data(val['owner'])[0] if val['owner'] else [],
            "weekly_goals_html": w_goal_url,
            "weekly_learnings_html": w_learn_url,
            "overall_progress":calculate_overall_progress(week_data,12),
            "issue_url":val['html_issue_url'],
            "pr_details":None,
            "weekly_goals":week_data,
            "weekly_learns":week_data_formatter(plain_text_wurl,"Learnings")
        }
        
        pr_Data = SUPABASE_DB.client.table('dmp_pr_updates').select('*').eq('repo', val['repo']).eq('issue_number_title',issue).execute()
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
        return jsonify({'error': str(e), 'traceback': error_traceback}), 200
