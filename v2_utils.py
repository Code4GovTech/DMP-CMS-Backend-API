import logging,re,markdown2

# Func to create name and link for all mentors and contributors
def define_link_data(usernames):
    try:
        res = []
        if type(usernames) == list:
            for username in usernames:
                val = {}
                val['name'] = username
                val['link'] = "https://github.com/" + username
                res.append(val)
        if type(usernames) == str:
            if usernames[0]=="@":
                usernames = usernames[1:]
            val = {}
            val['name'] = usernames
            val['link'] = "https://github.com/" + usernames
            res.append(val)
                    
        return res
    
    except Exception as e:
        logging.info(f"{e}---define_link_data")
        return []
        
        
  
def week_data_formatter(html_content, type):
    
    try:
        # Use regex to find week titles (e.g., Week 1, Week 2) and their corresponding task lists
        week_matches = re.findall(r'(Week \d+)', html_content)
        tasks_per_week = re.split(r'Week \d+', html_content)[1:]  # Split the content by weeks and skip the first empty split

        weekly_updates = []

        if type == "Learnings":
            for i, week in enumerate(week_matches):
                task_list_html = tasks_per_week[i] if i < len(tasks_per_week) else ""
                weekly_updates.append({
                    'week': i + 1,
                    'content': task_list_html.strip()
                })
            return weekly_updates

        else:
            for i, week in enumerate(week_matches):
                task_list_html = tasks_per_week[i] if i < len(tasks_per_week) else ""
                
                # Adjust regex to capture tasks regardless of the tags around them
                tasks = re.findall(r'\[(x|X| )\]\s*(.*?)</?li>', task_list_html, re.DOTALL)
                
                total_tasks = len(tasks)
                completed_tasks = sum(1 for task in tasks if task[0] in ['x', 'X'])
                task_list = [{"content": task[1].strip(), "checked": task[0] in ['x', 'X']} for task in tasks]
                
                avg = round((completed_tasks / total_tasks) * 100) if total_tasks != 0 else 0
                
                weekly_updates.append({
                    'week': i + 1,
                    'progress': avg,
                    'tasks': task_list
                })

            return weekly_updates

    except Exception as e:
        print(f"Error: {e}")
        return []
        
        
def calculate_overall_progress(weekly_updates, default_weeks=12):
    try:
        total_progress = 0
        provided_weeks = len(weekly_updates)
        
        # Sum the progress of each provided week
        for week in weekly_updates:
            total_progress += week.get('progress', 0)
        
        # Add zero progress for the remaining weeks to reach the default weeks
        total_weeks = default_weeks
        remaining_weeks = default_weeks - provided_weeks
        total_progress += remaining_weeks * 0  # Adding zero progress for the remaining weeks
        
        # Calculate the average progress over the total number of weeks
        overall_progress = total_progress / total_weeks if total_weeks > 0 else 0
        
        return round(overall_progress, 2)
    except Exception as e:
        print(f"Error: {e}")
        return 0
    