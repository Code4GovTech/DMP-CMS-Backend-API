import logging,re,markdown

# Func to create name and link for all mentors and contributors
def define_link_data(usernames):
    try:
        res = []
        if type(usernames) == list:
            for username in usernames:
                val = {}
                if username[0]=="@":
                    username = username[1:]
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
        
def preprocess_nested_tags(text):
    try:        
        segments = re.split(r'(<[^>]+>)', text)
        tag_stack = []
        corrected_segments = []

        for segment in segments:
            if re.match(r'<[^/][^>]*>', segment):  # Opening tag
                tag_stack.append(segment)
                corrected_segments.append(segment)
            elif re.match(r'</[^>]+>', segment):  # Closing tag
                if tag_stack and tag_stack[-1][1:].split()[0] == segment[2:].split()[0]:
                    tag_stack.pop()
                    corrected_segments.append(segment)
                else:
                    continue  # Ignore unmatched closing tag
            else:
                corrected_segments.append(segment)

        while tag_stack:
            open_tag = tag_stack.pop()
            tag_name = re.match(r'<([^ ]+)', open_tag).group(1)
            corrected_segments.append(f'</{tag_name}>')

        return ''.join(corrected_segments)

    except Exception as e:
        print(e,"error in preprocess_nested_tags function")
        return text
    
    

def remove_unmatched_tags(text):
    try:
        # Preprocess text to handle unmatched nested tags
        text = preprocess_nested_tags(text)
        
        # Remove unmatched closing tags at the beginning of the string
        text = re.sub(r'^\s*</[^>]+>\s*', '', text)
        # Regex pattern to find matched or unmatched tags
        pattern = re.compile(r'(<([^>]+)>.*?</\2>)|(<[^/][^>]*>.*?)(?=<[^/][^>]*>|$)', re.DOTALL)
        matches = pattern.findall(text)
        
        #If get text without html tags
        if matches == []:
            return text
        
        cleaned_text = ''
        open_tags = []
        
        for match in matches:
            if match[0]:  # Full matched <tag>...</tag> pairs
                cleaned_text += match[0]
            elif match[2]:  # Unmatched opening <tag> tags
                # Add the tag to the list of open tags
                tag = re.match(r'<([^/][^>]*)>', match[2])
                if tag:
                    tag_name = tag.group(1).split()[0]
                    open_tags.append(tag_name)
                cleaned_text += match[2]

        # Close any unmatched opening tags
        while open_tags:
            tag = open_tags.pop()
            cleaned_text += f'</{tag}>'

        # Remove extra unmatched angle brackets
        cleaned_text = re.sub(r'>+', '>', cleaned_text)
        cleaned_text = re.sub(r'<+', '<', cleaned_text)
        
        #For front end renders add ul tags 
        if not cleaned_text.strip().startswith("<ul>"):
            return f"<ul>{cleaned_text}</ul>"

        return cleaned_text
    
    except Exception as e:
        print(e)
        return text




  
def week_data_formatter(html_content, type):
    
    try:
        # Use regex to find week titles (e.g., Week 1, Week 2) and their corresponding task lists
        week_matches = re.findall(r'Week\s*-?\s*\d+', html_content)
        tasks_per_week = re.split(r'Week\s*-?\s*\d+', html_content)[1:]  # Split the content by weeks and skip the first empty split

        weekly_updates = []

        if type == "Learnings":
            # tasks_per_week = re.split(r'<h3>Week \d+</h3>', html_content)[1:]
            tasks_per_week = re.split(r'Week\s*-?\s*\d+', html_content)[1:]
            tasks_per_week = [tasks_per_week[i] for i in range(0, len(tasks_per_week))]
            for i, week in enumerate(week_matches):
                task_list_html = tasks_per_week[i] if i < len(tasks_per_week) else ""
                weekly_updates.append({
                    'week': i + 1,
                    'content': remove_unmatched_tags(task_list_html)
                  
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
    