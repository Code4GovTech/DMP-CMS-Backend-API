import logging,re,markdown2

# Func to create name and link for all mentors and contributors
def define_mentors_data(mentors):
    try:
        res = []
        
        if type(mentors) == list:
            for ment in mentors:
                val = {}
                val['name'] = ment
                val['link'] = "https://github.com/" + ment
                res.append(val)
        if type(mentors) == str:
            val = {}
            val['name'] = mentors
            val['link'] = "https://github.com/" + mentors
            res.append(val)
                    
        return res
    
    except Exception as e:
        logging.info(f"{e}---define_mentors")
        return []
        
        
        
def week_data_formatter(html_content,type):
    try:
        # Find all weeks
        week_matches = re.findall(r'<h2>(Week \d+)</h2>', html_content)
        tasks_per_week = re.findall(r'<h2>Week \d+</h2>\s*<ul>(.*?)</ul>', html_content, re.DOTALL)
        
        weekly_updates = []
        total_tasks = 0
        
        if type == "Learnings":
            for i, week in enumerate(week_matches):
                
                try:
                    task_list_html = tasks_per_week[i]
                except Exception as e:
                    task_list_html = ""
                    
                weekly_updates.append({
                    'week': i+1,
                    'content':task_list_html
                })

            return weekly_updates
        
        else:            
            for i, week in enumerate(week_matches):
                try:
                    task_list_html = tasks_per_week[i]
                except Exception as e:
                    task_list_html = ""
                
                tasks = re.findall(r'\[(x| )\] (.*?)</li>', task_list_html, re.DOTALL)
                
                total_tasks = len(tasks)
                completed_tasks = sum(1 for task in tasks if task[0] == 'x')
                task_list = [{"content":i[1],"checked":True if i[0]=='x' else False} for i in tasks]

                
                avg = round((completed_tasks / total_tasks) * 100) if total_tasks != 0 else 0
                
                weekly_updates.append({
                    'week': i+1,
                    # 'total_tasks': total_tasks,
                    # 'completed_tasks': completed_tasks,
                    'progress': avg,
                    'tasks':task_list
                })
                
            

            response = {
                'number_of_weeks': len(week_matches),
                'weekly_updates': weekly_updates
            }
            
            #FIND OVERALL PROGRESS
            
          

            return weekly_updates
           
        
    except Exception as e:
        return []
        
        
def calculate_overall_progress(weekly_updates, default_weeks=12):
    try:
        total_progress = 0
        provided_weeks = len(weekly_updates)
        
        # Sum the progress of each provided week
        for week in weekly_updates:
            total_progress += week['progress']
        
        # Add zero progress for the remaining weeks to reach the default weeks
        total_weeks = default_weeks
        remaining_weeks = default_weeks - provided_weeks
        total_progress += remaining_weeks * 0  # Adding zero progress for the remaining weeks
        
        # Calculate the average progress over the total number of weeks
        overall_progress = total_progress / total_weeks if total_weeks > 0 else 0
        
        return round(overall_progress, 2)
    except Exception as e:
        return 0
    