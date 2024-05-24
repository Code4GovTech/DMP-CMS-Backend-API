from flask import Flask, jsonify
from db import SupabaseInterface
from collections import defaultdict

app = Flask(__name__)


@app.route('/api/greeting', methods=['GET'])
def greeting():
    response = {
        'message': 'Hello, welcome to my API!'
    }
    return jsonify(response)

@app.route('/api/get-data', methods=['GET'])
def get_data():
    # Fetch data from Supabase
    try:
        import pdb;pdb.set_trace()
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
    return grouped_data

#DMP - CMS API's

@app.route('/api/issues', methods=['GET'])
def get_issues():
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').execute()
        data = response.data
        grouped_data = group_by_owner(data)
        return jsonify(grouped_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/issues/<owner>', methods=['GET'])
def get_issues_by_owner(owner):
    # Fetch data from Supabase
    try:
        import pdb;pdb.set_trace()
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('owner', owner).execute()
        
        if not response.data:
            return jsonify({'error': "No data found"}), 500

        data = response.data              
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/issues/<owner>/<issue>', methods=['GET'])
def get_issues_by_owner_id(owner,issue):
    # Fetch data from Supabase
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('owner', owner).eq('issue_number', issue).execute()
        
        if not response.data:
            return jsonify({'error': "No data found"}), 500

        data = response.data              
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
